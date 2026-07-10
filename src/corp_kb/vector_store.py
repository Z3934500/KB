from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .documents import chunk_documents
from .embeddings import HashingEmbedder, cosine
from .models import Chunk, Document, QueryFilters, RetrievedChunk


class SQLiteVectorStore:
    def __init__(self, db_path: Path, embedder: HashingEmbedder) -> None:
        self.db_path = db_path
        self.embedder = embedder
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                  document_id TEXT PRIMARY KEY,
                  title TEXT NOT NULL,
                  source_uri TEXT NOT NULL,
                  metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                  chunk_id TEXT PRIMARY KEY,
                  document_id TEXT NOT NULL,
                  title TEXT NOT NULL,
                  source_uri TEXT NOT NULL,
                  department TEXT,
                  confidentiality TEXT,
                  text TEXT NOT NULL,
                  metadata_json TEXT NOT NULL,
                  embedding_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_department ON chunks(department)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_confidentiality ON chunks(confidentiality)")

    def reset(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM documents")

    def index_documents(self, documents: list[Document], reset: bool = False) -> dict[str, int]:
        if reset:
            self.reset()
        chunks = chunk_documents(documents)
        with self.connect() as conn:
            for document in documents:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO documents(document_id, title, source_uri, metadata_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        document.document_id,
                        document.title,
                        document.source_uri,
                        json.dumps(document.metadata, sort_keys=True),
                    ),
                )
            for chunk in chunks:
                embedding = self.embedder.embed(chunk.text)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunks(
                      chunk_id, document_id, title, source_uri, department, confidentiality,
                      text, metadata_json, embedding_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.title,
                        chunk.source_uri,
                        chunk.metadata.get("department"),
                        chunk.metadata.get("confidentiality"),
                        chunk.text,
                        json.dumps(chunk.metadata, sort_keys=True),
                        json.dumps(embedding),
                    ),
                )
        return {"documents": len(documents), "chunks": len(chunks)}

    def count_chunks(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])

    def search(self, question: str, top_k: int, filters: QueryFilters | None = None) -> list[RetrievedChunk]:
        filters = filters or QueryFilters()
        where: list[str] = []
        params: list[str] = []
        if filters.department:
            where.append("LOWER(department) = LOWER(?)")
            params.append(filters.department)
        if filters.confidentiality:
            where.append("LOWER(confidentiality) = LOWER(?)")
            params.append(filters.confidentiality)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        query_vector = self.embedder.embed(question)

        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM chunks
                {where_sql}
                """,
                tuple(params),
            ).fetchall()

        scored: list[RetrievedChunk] = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            metadata = json.loads(row["metadata_json"])
            chunk = Chunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                title=row["title"],
                source_uri=row["source_uri"],
                text=row["text"],
                metadata=metadata,
            )
            scored.append(RetrievedChunk(chunk=chunk, score=cosine(query_vector, embedding), rank=0))

        scored.sort(key=lambda item: item.score, reverse=True)
        return [
            RetrievedChunk(chunk=item.chunk, score=item.score, rank=index + 1)
            for index, item in enumerate(scored[:top_k])
        ]
