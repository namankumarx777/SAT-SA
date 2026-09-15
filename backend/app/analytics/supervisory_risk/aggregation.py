from __future__ import annotations

from typing import Any

from app.analytics.supervisory_risk.config import (
    DIMENSION_WEIGHTS,
    DIMENSIONS,
    RISK_BAND_THRESHOLDS,
)
from app.analytics.supervisory_risk.correlation import CorrelatedGroupSignal
from app.analytics.supervisory_risk.inputs import StandardizedFinding
from app.analytics.supervisory_risk.models import EntityRisk, RiskBand


def _determine_risk_band(score: float) -> RiskBand:
    for band, (low, high) in RISK_BAND_THRESHOLDS.items():
        if low <= score <= high:
            return band  # type: ignore[return-value]
    return "CRITICAL" if score >= 75.0 else "LOW"


def aggregate_entity_risk(
    entity_id: str,
    dimension_scores: dict[str, float | None],
    unassessable_dimensions: set[str],
    group_signals: list[CorrelatedGroupSignal],
    entity_findings: list[StandardizedFinding],
    entity_metadata: dict[str, Any],
) -> EntityRisk:
    """Perform Level 2 aggregation to produce the bounded overall supervisory risk indicator and metadata."""
    assessable_dims = 0
    weighted_score_sum = 0.0
    assessable_weight_sum = 0.0

    for dim in DIMENSIONS:
        weight = DIMENSION_WEIGHTS.get(dim, 0.10)
        score = dimension_scores.get(dim)
        if dim not in unassessable_dimensions and score is not None:
            assessable_dims += 1
            assessable_weight_sum += weight
            weighted_score_sum += weight * score

    total_dims = len(DIMENSIONS)
    coverage = round(assessable_dims / total_dims, 2)

    # Normalize overall score over assessable weights
    if assessable_weight_sum > 0:
        overall_score = min(100.0, max(0.0, round(weighted_score_sum / assessable_weight_sum, 2)))
    else:
        overall_score = 0.0

    risk_band = _determine_risk_band(overall_score)

    # Identify top risk dimension and top reason among valid assessable dimensions
    valid_scores = {k: v for k, v in dimension_scores.items() if v is not None and k not in unassessable_dimensions}
    top_dim = max(valid_scores.items(), key=lambda item: item[1]) if valid_scores else ("None", 0.0)
    if top_dim[1] > 0:
        top_risk_dimension = top_dim[0]
        # Find the group signal driving this dimension
        driving_signals = [gs for gs in group_signals if gs.dimension == top_risk_dimension]
        if driving_signals:
            top_gs = max(driving_signals, key=lambda gs: gs.final_value)
            top_reason = (
                f"{top_risk_dimension} concern: {top_gs.group_id} score {top_gs.final_value:.1f} "
                f"({top_gs.corroboration_level} corroboration via {', '.join(top_gs.participating_detectors)})."
            )
        else:
            top_reason = f"Elevated {top_risk_dimension} score ({top_dim[1]:.1f}/100)."
    else:
        top_risk_dimension = "None"
        top_reason = "No material operational risks or execution gaps identified."

    # Evidence strength summary
    ev_counts: dict[str, int] = {}
    for f in entity_findings:
        st = f.evidence_strength if f.evidence_strength else "Unannotated"
        ev_counts[st] = ev_counts.get(st, 0) + 1
    ev_summary_parts = [f"{k}: {v}" for k, v in sorted(ev_counts.items())]
    evidence_strength_summary = ", ".join(ev_summary_parts) if ev_summary_parts else "No findings"

    # Corroboration summary
    corrob_parts = [
        f"{gs.group_id} ({gs.corroboration_level})"
        for gs in group_signals
        if gs.corroboration_level in ("Moderate", "Strong")
    ]
    corroboration_summary = (
        f"Corroborated groups: {', '.join(corrob_parts)}"
        if corrob_parts
        else "No multi-phase corroborated groups"
    )

    return EntityRisk(
        entity_id=entity_id,
        escalation_score=dimension_scores.get("Escalation", 0.0),
        investigation_score=dimension_scores.get("Investigation", 0.0),
        remediation_score=dimension_scores.get("Remediation", 0.0),
        monitoring_score=dimension_scores.get("Monitoring", 0.0),
        operational_discipline_score=dimension_scores.get("Operational Discipline", 0.0),
        cyber_resilience_score=dimension_scores.get("Cyber Resilience", 0.0),
        overall_score=overall_score,
        risk_band=risk_band,
        assessment_coverage=coverage,
        assessable_dimensions=assessable_dims,
        total_dimensions=total_dims,
        evidence_strength_summary=evidence_strength_summary,
        corroboration_summary=corroboration_summary,
        top_risk_dimension=top_risk_dimension,
        top_reason=top_reason,
        supporting_finding_count=len(entity_findings),
    )
