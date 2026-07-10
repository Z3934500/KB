from __future__ import annotations

import argparse
import json
import sys

from .architecture import (
    cicd_tool_tradeoffs,
    deployment_architecture,
    gpu_tradeoffs,
    runner_placement_tradeoffs,
    tier_catalog,
)
from .engines import answer_to_dict, engine_for_tier
from .models import QueryFilters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Corporate knowledge-base PoC CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Index sample documents")
    ingest.add_argument("--tier", choices=["lightweight", "medium", "heavy"], default="medium")
    ingest.add_argument("--no-reset", action="store_true")
    ingest.add_argument("--gpu", action="store_true")

    query = subparsers.add_parser("query", help="Ask a question")
    query.add_argument("question")
    query.add_argument("--tier", choices=["lightweight", "medium", "heavy"], default="lightweight")
    query.add_argument("--department")
    query.add_argument("--confidentiality")
    query.add_argument("--top-k", type=int, default=4)
    query.add_argument("--gpu", action="store_true")

    subparsers.add_parser("tradeoffs", help="Print CI/CD and architecture trade-offs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "ingest":
        engine = engine_for_tier(args.tier, use_gpu=args.gpu)
        print(json.dumps(engine.ingest(reset=not args.no_reset), indent=2))
        return 0

    if args.command == "query":
        engine = engine_for_tier(args.tier, use_gpu=args.gpu)
        answer = engine.query(
            args.question,
            filters=QueryFilters(args.department, args.confidentiality),
            top_k=args.top_k,
        )
        print(json.dumps(answer_to_dict(answer), indent=2))
        return 0

    if args.command == "tradeoffs":
        payload = {
            "tiers": tier_catalog(),
            "cicd_tools": cicd_tool_tradeoffs(),
            "runner_placement": runner_placement_tradeoffs(),
            "deployment": deployment_architecture(),
            "gpu": gpu_tradeoffs(),
        }
        print(json.dumps(payload, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
