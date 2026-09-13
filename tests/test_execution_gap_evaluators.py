from __future__ import annotations

import polars as pl

from app.analytics.execution_gap.definitions import DETECTORS
from app.analytics.execution_gap.evaluators import evaluate_eg001, evaluate_eg002, evaluate_eg003, evaluate_eg004


def entity(**values: object) -> pl.DataFrame:
    defaults = {
        "entity_id": "E1", "critical_case_count": 10, "critical_escalated_case_count": 3,
        "critical_escalation_rate": 0.30, "critical_median_investigation_minutes": 40.0,
        "closed_case_count": 20, "remediated_case_count": 8, "remediation_rate": 0.40,
        "rapid_closure_count": 10, "rapid_closure_rate": 0.50,
    }
    defaults.update(values)
    return pl.DataFrame([defaults])


def test_eg001_materiality_population_and_direction_guards() -> None:
    findings, evidence = evaluate_eg001(DETECTORS["EG001"], {"entity_features": entity()})
    assert len(findings) == 1 and findings[0].absolute_gap == 0.3 and evidence
    assert not evaluate_eg001(DETECTORS["EG001"], {"entity_features": entity(critical_case_count=4)})[0]
    assert not evaluate_eg001(DETECTORS["EG001"], {"entity_features": entity(critical_escalation_rate=0.50)})[0]


def test_eg002_uses_configured_expectation_with_reference_context() -> None:
    frame = pl.concat([entity(entity_id="E1", critical_median_investigation_minutes=10.0), entity(entity_id="E2", critical_median_investigation_minutes=100.0), entity(entity_id="E3", critical_median_investigation_minutes=110.0)])
    findings, _ = evaluate_eg002(DETECTORS["EG002"], {"entity_features": frame})
    assert len(findings) == 1 and findings[0].entity_id == "E1"
    assert findings[0].baseline_type == "configured_expectation"
    assert findings[0].baseline_method == "configured_minimum"
    assert findings[0].baseline_value == 20.0
    assert findings[0].reference_value == 100.0
    no_gap = frame.with_columns(pl.when(pl.col("entity_id") == "E1").then(pl.lit(13.0)).otherwise(pl.col("critical_median_investigation_minutes")).alias("critical_median_investigation_minutes"))
    assert not evaluate_eg002(DETECTORS["EG002"], {"entity_features": no_gap})[0]


def test_eg003_and_eg004_apply_sample_and_gap_guards() -> None:
    findings, _ = evaluate_eg003(DETECTORS["EG003"], {"entity_features": pl.concat([entity(entity_id="E1", remediation_rate=0.40), entity(entity_id="E2", remediation_rate=0.80), entity(entity_id="E3", remediation_rate=0.85)])})
    assert len(findings) == 1
    assert findings[0].baseline_value == 0.75
    assert findings[0].baseline_type == "configured_expectation"
    assert not evaluate_eg003(DETECTORS["EG003"], {"entity_features": entity(closed_case_count=9)})[0]
    reference_only_gap = pl.concat([entity(entity_id="E1", remediation_rate=0.61), entity(entity_id="E2", remediation_rate=0.80), entity(entity_id="E3", remediation_rate=0.90)])
    assert not evaluate_eg003(DETECTORS["EG003"], {"entity_features": reference_only_gap})[0]
    rapid, _ = evaluate_eg004(DETECTORS["EG004"], {"entity_features": entity()})
    assert len(rapid) == 1
    assert not evaluate_eg004(DETECTORS["EG004"], {"entity_features": entity(rapid_closure_rate=0.20)})[0]
    assert not evaluate_eg004(DETECTORS["EG004"], {"entity_features": entity(closed_case_count=9)})[0]
