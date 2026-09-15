from __future__ import annotations

from typing import Any

from app.analytics.supervisory_risk.config import DIMENSIONS
from app.analytics.supervisory_risk.correlation import CorrelatedGroupSignal


def calculate_dimension_scores(
    entity_id: str,
    group_signals: list[CorrelatedGroupSignal],
    entity_metadata: dict[str, Any],
) -> tuple[dict[str, float | None], set[str]]:
    """Calculate bounded 0-100 scores for the six required operational dimensions.

    Returns:
        (dimension_scores, unassessable_dimensions)
    """
    dimension_scores: dict[str, float | None] = {d: 0.0 for d in DIMENSIONS}
    unassessable_dimensions: set[str] = set()

    # Dynamic data-availability baseline checks
    if int(entity_metadata.get("closed_case_count", 0)) == 0 and int(entity_metadata.get("case_count", 0)) == 0:
        unassessable_dimensions.add("Investigation")

    if int(entity_metadata.get("alert_count", 0)) == 0 and int(entity_metadata.get("case_count", 0)) == 0:
        unassessable_dimensions.add("Operational Discipline")

    if int(entity_metadata.get("total_assets", 0)) == 0 and int(entity_metadata.get("expected_monitored_assets", 0)) == 0:
        unassessable_dimensions.add("Monitoring")
        unassessable_dimensions.add("Remediation")

    if int(entity_metadata.get("critical_case_count", 0)) == 0 and int(entity_metadata.get("case_count", 0)) == 0 and int(entity_metadata.get("alert_count", 0)) == 0:
        unassessable_dimensions.add("Escalation")

    # Group correlated signals by target dimension
    signals_by_dim: dict[str, list[CorrelatedGroupSignal]] = {d: [] for d in DIMENSIONS}
    for gs in group_signals:
        if gs.dimension in signals_by_dim:
            signals_by_dim[gs.dimension].append(gs)

    for dim in DIMENSIONS:
        if dim in unassessable_dimensions:
            dimension_scores[dim] = None
            continue

        signals = signals_by_dim[dim]
        if not signals:
            dimension_scores[dim] = 0.0
            continue

        # If only one correlation group in this dimension
        if len(signals) == 1:
            dimension_scores[dim] = round(signals[0].final_value, 2)
        else:
            # When multiple distinct correlation groups are active within the same dimension
            # (e.g. In Investigation: both RAPID_CLOSURE and INVESTIGATION_EFFORT),
            # combine with diminishing returns: primary group + 20% of secondary groups, capped at 100.0.
            sorted_signals = sorted(signals, key=lambda s: s.final_value, reverse=True)
            primary_val = sorted_signals[0].final_value
            secondary_sum = sum(s.final_value for s in sorted_signals[1:])
            combined_val = min(100.0, primary_val + 0.20 * secondary_sum)
            dimension_scores[dim] = round(combined_val, 2)

    return dimension_scores, unassessable_dimensions
