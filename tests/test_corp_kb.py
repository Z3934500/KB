from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from corp_kb.architecture import cicd_tool_tradeoffs, deployment_architecture, gpu_tradeoffs, sizing_thresholds
from corp_kb.config import settings
from corp_kb.documents import corpus_profile
from corp_kb.engines import HeavyPrivateRagEngine, LightweightManagedKbEngine, MediumVectorDbEngine
from corp_kb.models import QueryFilters


class CorporateKbTest(unittest.TestCase):
    def test_lightweight_engine_answers_with_citation(self) -> None:
        engine = LightweightManagedKbEngine(settings.document_dir)
        result = engine.query("What should MVP1 use for a department knowledge assistant?")
        self.assertEqual(result.tier, "lightweight")
        self.assertGreaterEqual(len(result.citations), 1)
        self.assertIn("Managed-KB", result.answer)

    def test_medium_engine_indexes_sqlite_vectors_and_filters(self) -> None:
        db_path = ROOT / "data" / "runtime" / "test_vectors_medium.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()
        engine = MediumVectorDbEngine(settings.document_dir, db_path=db_path)
        counts = engine.ingest(reset=True)
        self.assertGreaterEqual(counts["documents"], 4)
        self.assertGreaterEqual(counts["chunks"], 4)

        result = engine.query(
            "Where should metadata filters be enforced?",
            filters=QueryFilters(department="platform"),
        )
        self.assertEqual(result.tier, "medium")
        self.assertGreaterEqual(len(result.citations), 1)
        self.assertTrue(all("documents/" in citation.source_uri for citation in result.citations))

    def test_heavy_engine_exposes_private_gpu_tradeoff(self) -> None:
        db_path = ROOT / "data" / "runtime" / "test_vectors_heavy.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        if db_path.exists():
            db_path.unlink()
        engine = HeavyPrivateRagEngine(settings.document_dir, db_path=db_path, use_gpu=True)
        engine.ingest(reset=True)
        result = engine.query("When should GPU be used?")
        self.assertEqual(result.tier, "heavy")
        self.assertTrue(result.metadata["gpu_enabled"])
        self.assertIn("Private GPU endpoint", result.answer)

    def test_tradeoff_catalogs_include_requested_tools(self) -> None:
        tools = {item["tool"] for item in cicd_tool_tradeoffs()}
        self.assertIn("GitLab CI", tools)
        self.assertIn("GitHub Actions", tools)
        self.assertIn("Jenkins", tools)
        self.assertIn("Maven", tools)
        self.assertIn("Azure DevOps", tools)
        self.assertIn("Databricks Asset Bundles (DAB)", tools)

        thresholds = {item["tier"]: item for item in sizing_thresholds()}
        self.assertEqual(thresholds["lightweight"]["chunks"], "up to about 50,000 chunks")
        self.assertEqual(thresholds["medium"]["documents"], "3,000-30,000 documents")

        profile = corpus_profile(settings.document_dir)
        self.assertGreaterEqual(profile["documents"], 4)
        self.assertIn(profile["recommended_tier"], {"lightweight", "medium", "heavy"})

        deployment = deployment_architecture()
        self.assertIn("mvp1", deployment)
        self.assertIn("heavy", deployment)
        self.assertIn("GPU", " ".join(gpu_tradeoffs()["use_gpu_when"]))


if __name__ == "__main__":
    unittest.main()
