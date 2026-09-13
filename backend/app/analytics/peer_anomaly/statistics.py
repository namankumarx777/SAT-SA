from __future__ import annotations

import polars as pl


def deviation(observed: float, peer_median: float) -> tuple[float, float | None]:
    absolute = abs(observed - peer_median)
    relative = None if peer_median == 0 else absolute / abs(peer_median)
    return absolute, relative


def material_peer_deviation(metric: str, observed: float, median: float) -> bool:
    if metric in {"critical_escalation_rate", "remediation_rate", "rapid_closure_rate", "monitoring_coverage_rate", "repeat_alert_event_rate"}:
        return abs(observed - median) >= 0.15
    if metric == "critical_median_investigation_minutes":
        return median > 0 and (observed <= median * 0.5 or observed >= median * 1.5)
    if metric in {"alerts_per_asset", "cases_per_asset"}:
        return median > 0 and (observed <= median * 0.5 or observed >= median * 2.0)
    return False
