from __future__ import annotations

from pathlib import Path
import polars as pl
import pytest

from app.analytics.supervisory_risk.inputs import (
    StandardizedFinding,
    load_upstream_bundle,
    _format_timestamp,
)


def test_format_timestamp() -> None:
    from datetime import datetime, timezone
    dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert "2025-06-15" in _format_timestamp(dt)
    assert _format_timestamp("2025-06-15T12:00:00") == "2025-06-15T12:00:00"
    assert _format_timestamp(None) == ""


def test_load_upstream_bundle_from_processed() -> None:
    root = Path("data/processed")
    bundle = load_upstream_bundle(root)

    # 1. Entities loaded from Phase 4
    assert len(bundle.entities) == 12
    assert "CSE-001" in bundle.entities
    assert "critical_case_count" in bundle.entities["CSE-001"]

    # 2. Findings loaded across phases
    assert bundle.phase_counts["phase5"] > 0
    assert bundle.phase_counts["phase6"] > 0
    assert bundle.phase_counts["phase7"] > 0
    assert bundle.phase_counts["phase8"] > 0

    total_findings = sum(bundle.phase_counts.values())
    assert len(bundle.findings) == total_findings

    # 3. Timestamp normalization (all strings, non-empty)
    for f in bundle.findings:
        assert isinstance(f.created_at, str)
        assert len(f.created_at) > 0

    # 4. Phase-specific fields preserved
    phase6_findings = [f for f in bundle.findings if f.source_phase == "phase6"]
    assert any(f.gap_value is not None for f in phase6_findings)

    phase8_anomalies = [f for f in bundle.findings if f.rule_id == "AN001"]
    assert len(phase8_anomalies) > 0
    assert phase8_anomalies[0].anomaly_score is not None

    # 5. Evidence linkage
    assert len(bundle.evidence_by_finding) > 0
    sample_finding_id = bundle.findings[0].id
    # Some findings should have traceable evidence
    ev_count = sum(len(evs) for evs in bundle.evidence_by_finding.values())
    assert ev_count > 0
