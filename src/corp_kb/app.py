from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .architecture import (
    cicd_tool_tradeoffs,
    deployment_architecture,
    document_cleaning_rules,
    gpu_tradeoffs,
    runner_placement_tradeoffs,
    sizing_thresholds,
    tier_catalog,
)
from .config import settings
from .documents import corpus_profile
from .engines import answer_to_dict, engine_for_tier
from .models import QueryFilters


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    tier: Literal["lightweight", "medium", "heavy"] = "lightweight"
    department: str | None = None
    confidentiality: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)
    use_gpu: bool = False


class IngestRequest(BaseModel):
    tier: Literal["lightweight", "medium", "heavy"] = "medium"
    reset: bool = True
    use_gpu: bool = False


app = FastAPI(
    title="Corporate Knowledge Base Automation PoC",
    version="0.1.0",
    description="Three-tier enterprise knowledge-base automation PoC.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "document_dir": str(settings.document_dir),
        "sqlite_path": str(settings.sqlite_path),
        "tiers": ["lightweight", "medium", "heavy"],
    }


@app.get("/api/tiers")
def tiers() -> list[dict[str, object]]:
    return tier_catalog()


@app.post("/api/ingest")
def ingest(request: IngestRequest) -> dict[str, int]:
    try:
        engine = engine_for_tier(request.tier, use_gpu=request.use_gpu)
        return engine.ingest(reset=request.reset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/query")
def query(request: QueryRequest) -> dict:
    try:
        engine = engine_for_tier(request.tier, use_gpu=request.use_gpu)
        answer = engine.query(
            request.question,
            filters=QueryFilters(
                department=request.department,
                confidentiality=request.confidentiality,
            ),
            top_k=request.top_k,
        )
        return answer_to_dict(answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/cicd/tradeoffs")
def cicd_tradeoffs() -> dict[str, object]:
    return {
        "tools": cicd_tool_tradeoffs(),
        "runner_placement": runner_placement_tradeoffs(),
    }


@app.get("/api/corpus/profile")
def corpus_profile_api() -> dict[str, object]:
    return corpus_profile(settings.document_dir)


@app.get("/api/architecture")
def architecture() -> dict[str, object]:
    return {
        "tiers": tier_catalog(),
        "sizing_thresholds": sizing_thresholds(),
        "document_cleaning_rules": document_cleaning_rules(),
        "deployment": deployment_architecture(),
        "gpu": gpu_tradeoffs(),
    }
