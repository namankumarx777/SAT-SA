from __future__ import annotations

import polars as pl

from app.analytics.execution_gap.models import BaselineResult


def configured_baseline(value: float, method: str = "configured_supervisory_expectation") -> BaselineResult:
    """Return an explicit supervisory expectation."""
    return BaselineResult(value=value, method=method, baseline_type="configured_expectation", population_size=0)


def population_median(entity_features: pl.DataFrame, metric: str, population_column: str, minimum_population: int) -> BaselineResult:
    """Return a robust median from entities with sufficient observations."""
    reference = entity_features.filter(
        (pl.col(population_column) >= minimum_population)
        & pl.col(metric).is_not_null()
    ).select(metric)
    if reference.height == 0:
        return BaselineResult(value=None, method="population_median", baseline_type="reference_statistic", population_size=0)
    return BaselineResult(value=float(reference[metric].median()), method="population_median", baseline_type="reference_statistic", population_size=reference.height)


def evidence_strength_for_gap(population_size: int, absolute_gap: float) -> str:
    """Map population and gap magnitude to evidence strength, not statistical confidence."""
    if population_size >= 20 and absolute_gap >= 0.25:
        return "High"
    if population_size >= 10 or absolute_gap >= 0.20:
        return "Medium"
    return "Low"


def confidence_for_gap(population_size: int, absolute_gap: float) -> str:
    """Backward-compatible alias for evidence_strength_for_gap."""
    return evidence_strength_for_gap(population_size, absolute_gap)
