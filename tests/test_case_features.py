from __future__ import annotations

from datetime import datetime

import polars as pl

from app.analytics.features.case_features import build_case_features


def test_case_durations_escalation_and_text_features() -> None:
    cases = pl.DataFrame({
        "id": ["C1", "C2"], "entity_id": ["E1", "E1"], "alert_id": ["A1", "A2"],
        "opened_at": [datetime(2025, 1, 1), datetime(2025, 1, 2)],
        "closed_at": [datetime(2025, 1, 1, 2), None],
        "investigation_text": ["Reviewed endpoint activity", ""], "disposition": ["Benign", "True Positive"],
        "escalated": [True, False], "remediation_recorded": [True, False],
    })
    escalations = pl.DataFrame({"id": ["E1"], "entity_id": ["E1"], "case_id": ["C1"], "created_at": [datetime(2025, 1, 1, 1)]})
    features = build_case_features(cases, escalations).sort("id")
    assert features["investigation_minutes"].to_list() == [120.0, None]
    assert features["escalation_delay_minutes"].to_list() == [60.0, None]
    assert features["is_escalated"].to_list() == [True, False]
    assert features["is_remediated"].to_list() == [True, False]
    assert features["investigation_word_count"].to_list() == [3, 0]
    assert features["has_investigation_text"].to_list() == [True, False]
