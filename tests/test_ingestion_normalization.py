from __future__ import annotations

import polars as pl

from app.ingestion.normalizers import normalize_frame


def test_aliases_booleans_and_whitespace_are_normalized() -> None:
    result = normalize_frame(
        pl.DataFrame({
            "alert_id": [" A-1 "],
            "entity_id": [" CSE-001 "],
            "asset_id": [" AST-1 "],
            "detected_at": ["2025-01-01T12:00:00"],
            "severity_level": [" High "],
            "source": ["EDR"],
            "status": [" Open "],
            "analyst_name": ["analyst"],
        }),
        "alerts",
    )
    assert result.frame["id"].to_list() == ["A-1"]
    assert result.frame["severity"].to_list() == ["High"]
    assert result.frame["timestamp"].dtype == pl.Datetime
    assert any(issue.error_type == "UNKNOWN_COLUMN" for issue in result.issues)


def test_boolean_alias_and_values_are_normalized() -> None:
    result = normalize_frame(
        pl.DataFrame({
            "case_id": ["CASE-1"], "entity_id": ["CSE-001"], "alert_id": ["ALT-1"],
            "opened_at": ["2025-01-01T00:00:00"], "investigation_notes": ["Reviewed"],
            "disposition": ["Benign"], "escalated_flag": ["yes"],
            "remediation_recorded": ["0"],
        }),
        "cases",
    )
    assert result.frame["escalated"].to_list() == [True]
    assert result.frame["remediation_recorded"].to_list() == [False]
    assert not [issue for issue in result.issues if issue.severity == "error"]


def test_invalid_types_and_timestamps_are_reported() -> None:
    result = normalize_frame(
        pl.DataFrame({
            "id": ["ALT-1"], "entity_id": ["CSE-001"], "asset_id": ["AST-1"],
            "timestamp": ["not-a-date"], "severity": ["High"], "source": ["EDR"],
            "status": ["Open"], "acknowledged_at": [None], "closed_at": [None], "case_id": [None],
        }),
        "alerts",
    )
    assert any(issue.error_type == "INVALID_TIMESTAMP" for issue in result.issues)
