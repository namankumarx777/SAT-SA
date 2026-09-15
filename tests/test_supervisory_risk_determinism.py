from __future__ import annotations

import ast
from pathlib import Path

import duckdb
import polars as pl
import pytest

from app.analytics.supervisory_risk.config import ANOMALY_SCORE_CEILING
from app.analytics.supervisory_risk.engine import run_supervisory_risk
from app.analytics.supervisory_risk.inputs import StandardizedFinding
from app.analytics.supervisory_risk.normalization import normalize_finding_signal


def test_determinism_across_two_runs(tmp_path: Path) -> None:
    output_run1 = tmp_path / "run1"
    output_run2 = tmp_path / "run2"

    input_dir = Path("data/processed")
    run_supervisory_risk(input_dir, output_dir=output_run1, dataset_id="test_run1")
    run_supervisory_risk(input_dir, output_dir=output_run2, dataset_id="test_run2")

    # 1. Compare entity_risk
    df_risk1 = pl.read_parquet(output_run1 / "entity_risk.parquet")
    df_risk2 = pl.read_parquet(output_run2 / "entity_risk.parquet")
    assert df_risk1.equals(df_risk2)

    # 2. Compare risk_contributions
    df_contrib1 = pl.read_parquet(output_run1 / "risk_contributions.parquet")
    df_contrib2 = pl.read_parquet(output_run2 / "risk_contributions.parquet")
    assert df_contrib1.equals(df_contrib2)

    # 3. Compare review_queue
    df_queue1 = pl.read_parquet(output_run1 / "review_queue.parquet")
    df_queue2 = pl.read_parquet(output_run2 / "review_queue.parquet")
    assert df_queue1.equals(df_queue2)


def test_an001_cannot_dominate_deterministic_risk() -> None:
    # Extreme anomaly score from Isolation Forest (e.g. 0.99)
    finding = StandardizedFinding(
        id="f_an001", rule_id="AN001", entity_id="CSE-ANOMALY", source_phase="phase8",
        finding_type="Unknown Anomaly", severity="Medium", confidence="Low",
        evidence_strength="Low", confidence_type="evidence_strength",
        title="Unusual Operational Profile", summary="Outlier", rationale="IForest",
        status="OPEN", created_at="2025-01-01", anomaly_score=0.99, anomaly_rank=1,
    )
    sig = normalize_finding_signal(finding, {"total_assets": 50}, [finding])

    # Must NOT exceed the configured ceiling
    assert sig.normalized_value <= ANOMALY_SCORE_CEILING
    assert sig.normalized_value <= 25.0
    # Must explicitly state non-probability in rationale
    assert "not a probability" in sig.rationale


def test_an001_different_negative_scores_do_not_collapse() -> None:
    """Ensure two different anomaly strengths (even with negative decision scores) produce distinct normalized scores."""
    f1 = StandardizedFinding(
        id="f_an001_rank1", rule_id="AN001", entity_id="CSE-011", source_phase="phase8",
        finding_type="Unknown Anomaly", severity="High", confidence="Low",
        evidence_strength="Low", confidence_type="evidence_strength",
        title="Unusual Operational Profile", summary="Rank 1 anomaly", rationale="IForest",
        status="OPEN", created_at="2025-01-01", anomaly_score=-0.0177, anomaly_rank=1,
        contributing_deviations={"critical_escalation_rate": 0.35, "remediation_rate": -0.40},
    )
    f2 = StandardizedFinding(
        id="f_an001_rank2", rule_id="AN001", entity_id="CSE-012", source_phase="phase8",
        finding_type="Unknown Anomaly", severity="Medium", confidence="Low",
        evidence_strength="Low", confidence_type="evidence_strength",
        title="Unusual Operational Profile", summary="Rank 2 anomaly", rationale="IForest",
        status="OPEN", created_at="2025-01-01", anomaly_score=-0.0036, anomaly_rank=2,
        contributing_deviations={"critical_escalation_rate": 0.10},
    )

    all_findings = [f1, f2]
    sig1 = normalize_finding_signal(f1, {"total_assets": 50}, all_findings)
    sig2 = normalize_finding_signal(f2, {"total_assets": 50}, all_findings)

    # Both must be bounded [0, 25]
    assert 0.0 <= sig1.normalized_value <= 25.0
    assert 0.0 <= sig2.normalized_value <= 25.0
    # Must preserve ordering: Rank 1 > Rank 2
    assert sig1.normalized_value > sig2.normalized_value
    # Must NOT collapse to the same constant floor (e.g. 10.0)
    assert sig1.normalized_value != sig2.normalized_value
    assert sig1.normalized_value != 10.0 or sig2.normalized_value != 10.0



def test_duckdb_and_polars_compatibility() -> None:
    path_risk = Path("data/processed/supervisory_risk-final/entity_risk.parquet")
    path_queue = Path("data/processed/supervisory_risk-final/review_queue.parquet")
    path_contrib = Path("data/processed/supervisory_risk-final/risk_contributions.parquet")

    assert path_risk.is_file()
    assert path_queue.is_file()
    assert path_contrib.is_file()

    # DuckDB SQL execution
    con = duckdb.connect()
    res = con.execute(f"SELECT entity_id, overall_score, risk_band FROM '{path_risk.as_posix()}' WHERE overall_score > 30").fetchall()
    assert len(res) > 0

    res_q = con.execute(f"SELECT count(*) FROM '{path_queue.as_posix()}' WHERE priority = 'HIGH'").fetchone()
    assert res_q[0] > 0


def test_ground_truth_independence() -> None:
    """Phase 9 must not import or depend on synthetic generator ground-truth controls."""
    package_dir = Path("backend/app/analytics/supervisory_risk")
    for py_file in package_dir.glob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        parsed = ast.parse(code)
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "generate_synthetic" not in alias.name, f"Forbidden ground truth import in {py_file}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "generate_synthetic" not in module, f"Forbidden ground truth import in {py_file}"
        # Also check forbidden strings
        assert "GROUND_TRUTH_ENTITY_SETS" not in code
        assert "EXECUTION_GAP_ENTITIES" not in code
        assert "NEGATIVE_SPACE_ENTITIES" not in code
