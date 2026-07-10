from __future__ import annotations

from corp_kb.engines import MediumVectorDbEngine
from corp_kb.models import QueryFilters


QUESTIONS = [
    ("Where should metadata filters be enforced?", QueryFilters(department="platform")),
    ("When should GPU be used?", QueryFilters(department="ai-platform")),
]


def main() -> None:
    engine = MediumVectorDbEngine()
    engine.ingest(reset=True)
    failures: list[str] = []

    for question, filters in QUESTIONS:
        answer = engine.query(question, filters=filters)
        if not answer.citations:
            failures.append(question)

    if failures:
        raise SystemExit(f"RAG evaluation failed for: {failures}")

    print("RAG evaluation passed")


if __name__ == "__main__":
    main()
