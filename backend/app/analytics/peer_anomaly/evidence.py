from __future__ import annotations

from app.analytics.rules.evidence import make_evidence, make_finding
from app.analytics.rules.models import Evidence, Finding


def peer_finding(*, detector_id: str, entity_id: str, metric: str, observed: float, median: float, deviation: float, peer_count: int, cohort_key: str, strength: str, title: str, rationale: str) -> Finding:
    return make_finding(
        rule_id=detector_id, entity_id=entity_id, source_id=f"{cohort_key}|{metric}", finding_type="Peer Deviation",
        severity="Medium", confidence=strength, evidence_strength=strength, title=title,
        summary=f"{metric} differs materially from the peer reference median.", rationale=rationale,
        metric_name=metric, observed_value=observed, expected_value=None, population_size=peer_count,
        absolute_gap=deviation, relative_gap=None, baseline_method="peer_median", baseline_type="peer_reference",
        baseline_value=median, reference_value=median, gap_value=deviation, gap_direction="peer_deviation",
    )


def anomaly_finding(*, entity_id: str, score: float, rank: int, contributions: list[dict[str, object]], strength: str, rationale: str) -> Finding:
    return make_finding(
        rule_id="AN001", entity_id=entity_id, source_id=entity_id, finding_type="Unknown Anomaly",
        severity="Medium", confidence=strength, evidence_strength=strength, title="Unusual operational profile",
        summary="The entity's operational feature profile was unusual in the global population.", rationale=rationale,
        metric_name="anomaly_score", observed_value=score, population_size=None,
        baseline_method="isolation_forest", baseline_type="model_relative_unusualness",
        anomaly_score=score, anomaly_rank=rank, contributing_deviations=contributions,
    )


def add_feature_evidence(finding: Finding, source_type: str, source_id: str, values: dict[str, object], reason: str) -> list[Evidence]:
    return [make_evidence(finding, source_type, source_id, field, value, reason) for field, value in values.items()]
