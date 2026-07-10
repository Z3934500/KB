from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    source_uri: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    source_uri: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
    rank: int


@dataclass(frozen=True)
class Citation:
    rank: int
    title: str
    source_uri: str
    score: float
    chunk_id: str


@dataclass(frozen=True)
class QueryAnswer:
    tier: str
    question: str
    answer: str
    citations: list[Citation]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QueryFilters:
    department: str | None = None
    confidentiality: str | None = None

    def as_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if self.department:
            result["department"] = self.department
        if self.confidentiality:
            result["confidentiality"] = self.confidentiality
        return result
