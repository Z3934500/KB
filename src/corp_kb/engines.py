from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from .config import settings
from .documents import chunk_documents, load_documents
from .embeddings import HashingEmbedder, tokenize
from .models import Citation, QueryAnswer, QueryFilters, RetrievedChunk
from .vector_store import SQLiteVectorStore


class RagEngine(Protocol):
    tier: str

    def ingest(self, reset: bool = False) -> dict[str, int]:
        ...

    def query(self, question: str, filters: QueryFilters | None = None, top_k: int | None = None) -> QueryAnswer:
        ...


def citations_from_hits(hits: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            rank=hit.rank,
            title=hit.chunk.title,
            source_uri=hit.chunk.source_uri,
            score=round(hit.score, 4),
            chunk_id=hit.chunk.chunk_id,
        )
        for hit in hits
    ]


def extract_relevant_text(question: str, hits: list[RetrievedChunk], max_chars: int = 700) -> str:
    question_tokens = set(tokenize(question))
    selected: list[str] = []
    for hit in hits:
        sentences = [part.strip() for part in hit.chunk.text.replace("\n", " ").split(".") if part.strip()]
        matching = [
            sentence
            for sentence in sentences
            if question_tokens.intersection(tokenize(sentence))
        ]
        text = ". ".join(matching[:2]) if matching else hit.chunk.text[:240]
        selected.append(f"[{hit.rank}] {text.strip()}")
    answer_context = " ".join(selected)
    return answer_context[:max_chars]


def compose_grounded_answer(tier: str, question: str, hits: list[RetrievedChunk], note: str) -> QueryAnswer:
    if not hits:
        return QueryAnswer(
            tier=tier,
            question=question,
            answer=(
                "I do not have enough indexed knowledge to answer from the approved corpus. "
                "Route this question to a document owner or add the missing source document."
            ),
            citations=[],
            metadata={"mode": note, "fallback": True},
        )
    context = extract_relevant_text(question, hits)
    answer = (
        f"{note} Based on the retrieved knowledge, the answer is: {context}. "
        "Use the citations to verify the exact source before treating this as final policy."
    )
    return QueryAnswer(
        tier=tier,
        question=question,
        answer=answer,
        citations=citations_from_hits(hits),
        metadata={"mode": note, "fallback": False},
    )


class LightweightManagedKbEngine:
    tier = "lightweight"

    def __init__(self, document_dir=None) -> None:
        self.document_dir = document_dir or settings.document_dir

    def ingest(self, reset: bool = False) -> dict[str, int]:
        documents = load_documents(self.document_dir)
        chunks = chunk_documents(documents)
        return {
            "documents": len(documents),
            "chunks": len(chunks),
            "managed_storage": 1,
            "reset_requested": int(reset),
        }

    def query(self, question: str, filters: QueryFilters | None = None, top_k: int | None = None) -> QueryAnswer:
        filters = filters or QueryFilters()
        top_k = top_k or settings.default_top_k
        documents = load_documents(self.document_dir)
        chunks = chunk_documents(documents)
        query_tokens = set(tokenize(question))
        hits: list[RetrievedChunk] = []
        for chunk in chunks:
            if filters.department and chunk.metadata.get("department", "").lower() != filters.department.lower():
                continue
            if (
                filters.confidentiality
                and chunk.metadata.get("confidentiality", "").lower() != filters.confidentiality.lower()
            ):
                continue
            chunk_tokens = set(tokenize(chunk.text))
            overlap = len(query_tokens.intersection(chunk_tokens))
            score = overlap / max(1, len(query_tokens))
            if score > 0:
                hits.append(RetrievedChunk(chunk=chunk, score=score, rank=0))
        hits.sort(key=lambda item: item.score, reverse=True)
        ranked = [
            RetrievedChunk(chunk=item.chunk, score=item.score, rank=index + 1)
            for index, item in enumerate(hits[:top_k])
        ]
        return compose_grounded_answer(
            self.tier,
            question,
            ranked,
            "Managed-KB adapter: production maps to Bedrock RetrieveAndGenerate over S3 documents.",
        )


class MediumVectorDbEngine:
    tier = "medium"

    def __init__(self, document_dir=None, db_path=None, embedder: HashingEmbedder | None = None) -> None:
        self.document_dir = document_dir or settings.document_dir
        self.embedder = embedder or HashingEmbedder(settings.embedding_dimension)
        self.store = SQLiteVectorStore(db_path or settings.sqlite_path, self.embedder)

    def ingest(self, reset: bool = False) -> dict[str, int]:
        documents = load_documents(self.document_dir)
        result = self.store.index_documents(documents, reset=reset)
        result["vector_db"] = 1
        result["embedding_dimension"] = self.embedder.dimension
        return result

    def ensure_indexed(self) -> None:
        if self.store.count_chunks() == 0:
            self.ingest(reset=True)

    def query(self, question: str, filters: QueryFilters | None = None, top_k: int | None = None) -> QueryAnswer:
        self.ensure_indexed()
        hits = self.store.search(question, top_k or settings.default_top_k, filters or QueryFilters())
        return compose_grounded_answer(
            self.tier,
            question,
            hits,
            "Explicit vector DB adapter: local SQLite vector index, production maps to pgvector or OpenSearch.",
        )


class PrivateEndpointClient:
    def __init__(self, endpoint_url: str | None = None, use_gpu: bool = False) -> None:
        self.endpoint_url = endpoint_url
        self.use_gpu = use_gpu

    @property
    def runtime(self) -> str:
        if self.endpoint_url:
            return "private_gpu_endpoint" if self.use_gpu else "private_cpu_endpoint"
        return "local_private_endpoint_simulator_gpu" if self.use_gpu else "local_private_endpoint_simulator_cpu"

    def generate(self, question: str, hits: list[RetrievedChunk]) -> str:
        context = extract_relevant_text(question, hits, max_chars=520)
        accelerator = "GPU" if self.use_gpu else "CPU"
        return (
            f"Private {accelerator} endpoint response. "
            f"Grounded answer: {context}. "
            "This tier keeps model serving behind a private endpoint and preserves vector-search citations."
        )


class HeavyPrivateRagEngine:
    tier = "heavy"

    def __init__(
        self,
        document_dir=None,
        db_path=None,
        endpoint_url: str | None = None,
        use_gpu: bool = False,
    ) -> None:
        self.vector_engine = MediumVectorDbEngine(document_dir=document_dir, db_path=db_path)
        self.private_client = PrivateEndpointClient(endpoint_url=endpoint_url, use_gpu=use_gpu)

    def ingest(self, reset: bool = False) -> dict[str, int]:
        result = self.vector_engine.ingest(reset=reset)
        result["private_endpoint_ready"] = 1
        result["gpu_enabled"] = int(self.private_client.use_gpu)
        return result

    def query(self, question: str, filters: QueryFilters | None = None, top_k: int | None = None) -> QueryAnswer:
        self.vector_engine.ensure_indexed()
        hits = self.vector_engine.store.search(question, top_k or settings.default_top_k, filters or QueryFilters())
        if not hits:
            return compose_grounded_answer(
                self.tier,
                question,
                hits,
                "Private endpoint orchestration with vector retrieval.",
            )
        answer = self.private_client.generate(question, hits)
        return QueryAnswer(
            tier=self.tier,
            question=question,
            answer=answer,
            citations=citations_from_hits(hits),
            metadata={
                "runtime": self.private_client.runtime,
                "gpu_enabled": self.private_client.use_gpu,
                "fallback": False,
            },
        )


def engine_for_tier(tier: str, use_gpu: bool = False) -> RagEngine:
    normalized = tier.lower().strip()
    if normalized in {"light", "lightweight", "managed"}:
        return LightweightManagedKbEngine()
    if normalized in {"medium", "vector", "vectordb"}:
        return MediumVectorDbEngine()
    if normalized in {"heavy", "private", "gpu"}:
        return HeavyPrivateRagEngine(use_gpu=use_gpu)
    raise ValueError(f"Unsupported tier: {tier}")


def answer_to_dict(answer: QueryAnswer) -> dict:
    return {
        "tier": answer.tier,
        "question": answer.question,
        "answer": answer.answer,
        "citations": [asdict(citation) for citation in answer.citations],
        "metadata": answer.metadata,
    }
