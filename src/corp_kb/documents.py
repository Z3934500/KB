from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import Chunk, Document


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def stable_id(value: str, prefix: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def parse_metadata(raw_text: str) -> tuple[dict[str, str], str]:
    metadata: dict[str, str] = {}
    lines = raw_text.splitlines()
    body_start = 0

    for idx, line in enumerate(lines[:16]):
        stripped = line.strip()
        if not stripped:
            body_start = idx + 1
            break
        if ":" not in stripped:
            body_start = idx
            break
        key, value = stripped.split(":", 1)
        normalized_key = key.strip().lower().replace(" ", "_")
        metadata[normalized_key] = value.strip()
        body_start = idx + 1

    body = "\n".join(lines[body_start:]).strip() or raw_text.strip()
    return metadata, body


def title_from_text(path: Path, text: str, metadata: dict[str, str]) -> str:
    if metadata.get("title"):
        return metadata["title"]
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def load_documents(document_dir: Path) -> list[Document]:
    if not document_dir.exists():
        return []

    documents: list[Document] = []
    for path in sorted(document_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = parse_metadata(raw_text)
        rel_path = path.relative_to(document_dir).as_posix()
        title = title_from_text(path, body, metadata)
        documents.append(
            Document(
                document_id=stable_id(rel_path, "doc"),
                title=title,
                source_uri=f"documents/{rel_path}",
                text=body,
                metadata=metadata,
            )
        )
    return documents


def chunk_document(document: Document, chunk_words: int = 90, overlap_words: int = 18) -> list[Chunk]:
    words = re.findall(r"\S+", document.text)
    if not words:
        return []
    step = max(1, chunk_words - overlap_words)
    chunks: list[Chunk] = []

    for start in range(0, len(words), step):
        part = words[start : start + chunk_words]
        if not part:
            continue
        chunk_text = " ".join(part)
        chunk_id = stable_id(f"{document.document_id}:{start}:{chunk_text[:80]}", "chunk")
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                title=document.title,
                source_uri=document.source_uri,
                text=chunk_text,
                metadata=document.metadata,
            )
        )
        if start + chunk_words >= len(words):
            break
    return chunks


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document))
    return chunks


def normalized_tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_]+", text)}


def content_fingerprint(text: str) -> str:
    normalized = " ".join(sorted(normalized_tokens(text)))
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / len(left.union(right))


def duplicate_groups(documents: list[Document], near_duplicate_threshold: float = 0.82) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    exact: dict[str, list[Document]] = {}
    token_sets = {document.document_id: normalized_tokens(document.text) for document in documents}

    for document in documents:
        exact.setdefault(content_fingerprint(document.text), []).append(document)

    used: set[str] = set()
    for docs in exact.values():
        if len(docs) > 1:
            ids = [doc.document_id for doc in docs]
            used.update(ids)
            groups.append(
                {
                    "type": "exact",
                    "similarity": 1.0,
                    "document_ids": ids,
                    "titles": [doc.title for doc in docs],
                    "recommended_action": "Keep the newest approved source and mark the others as superseded aliases.",
                }
            )

    for index, left in enumerate(documents):
        if left.document_id in used:
            continue
        for right in documents[index + 1 :]:
            if right.document_id in used:
                continue
            similarity = jaccard_similarity(token_sets[left.document_id], token_sets[right.document_id])
            if similarity >= near_duplicate_threshold:
                used.add(left.document_id)
                used.add(right.document_id)
                groups.append(
                    {
                        "type": "near_duplicate",
                        "similarity": round(similarity, 4),
                        "document_ids": [left.document_id, right.document_id],
                        "titles": [left.title, right.title],
                        "recommended_action": "Review owner/effective_date; merge or keep one canonical source with aliases.",
                    }
                )
    return groups


def recommended_tier_for_counts(
    document_count: int,
    estimated_pages: int,
    estimated_chunks: int,
    duplicate_rate: float,
    departments: int,
) -> str:
    if (
        document_count <= 3000
        and estimated_pages <= 10000
        and estimated_chunks <= 50000
        and duplicate_rate < 0.10
        and departments <= 3
    ):
        return "lightweight"
    if (
        document_count <= 30000
        and estimated_pages <= 150000
        and estimated_chunks <= 500000
        and duplicate_rate < 0.30
        and departments <= 20
    ):
        return "medium"
    return "heavy"


def corpus_profile(document_dir: Path) -> dict[str, object]:
    documents = load_documents(document_dir)
    chunks = chunk_documents(documents)
    total_words = sum(len(re.findall(r"\S+", document.text)) for document in documents)
    estimated_pages = max(1, round(total_words / 500)) if documents else 0
    departments = {doc.metadata.get("department", "unknown") for doc in documents}
    groups = duplicate_groups(documents)
    duplicated_documents = {doc_id for group in groups for doc_id in group["document_ids"]}
    duplicate_rate = len(duplicated_documents) / len(documents) if documents else 0.0

    return {
        "documents": len(documents),
        "estimated_pages": estimated_pages,
        "estimated_chunks": len(chunks),
        "estimated_words": total_words,
        "departments": len(departments),
        "duplicate_groups": groups,
        "duplicate_rate": round(duplicate_rate, 4),
        "recommended_tier": recommended_tier_for_counts(
            len(documents),
            estimated_pages,
            len(chunks),
            duplicate_rate,
            len(departments),
        ),
        "assumptions": {
            "page_words": 500,
            "chunk_words": 90,
            "near_duplicate_jaccard_threshold": 0.82,
        },
    }
