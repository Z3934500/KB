from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    document_dir: Path = ROOT_DIR / "data" / "documents"
    runtime_dir: Path = ROOT_DIR / "data" / "runtime"
    sqlite_path: Path = ROOT_DIR / "data" / "runtime" / "corp_kb_vectors.sqlite"
    embedding_dimension: int = 96
    default_top_k: int = 4


settings = Settings()
