from __future__ import annotations

from datetime import datetime

import polars as pl

from app.analytics.negative_space.models import ObservationWindow


def observation_window(bundle: dict[str, pl.DataFrame]) -> ObservationWindow:
    """Find the inclusive usable observation range from alert and case timestamps."""
    timestamps: list[datetime] = []
    for table, column in (("alert_features", "timestamp"), ("case_features", "opened_at")):
        frame = bundle.get(table)
        if frame is not None and column in frame.columns:
            timestamps.extend(value for value in frame[column].drop_nulls().to_list() if isinstance(value, datetime))
    if not timestamps:
        return ObservationWindow(start=None, end=None, sufficient=False, reason="INSUFFICIENT_OBSERVATION_WINDOW")
    start, end = min(timestamps), max(timestamps)
    return ObservationWindow(start=start.isoformat(), end=end.isoformat(), sufficient=start < end)


def evidence_strength(population: int, magnitude: float, expectation_strength: str = "explicit") -> str:
    """Return evidence strength, not statistical confidence."""
    if population >= 20 and magnitude >= 0.25 and expectation_strength == "explicit":
        return "High"
    if population >= 5 and magnitude >= 0.10:
        return "Medium"
    return "Low"
