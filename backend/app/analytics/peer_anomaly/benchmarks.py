from __future__ import annotations

import polars as pl

from app.analytics.peer_anomaly.cohorts import COHORT_COLUMNS, MIN_COHORT_SIZE, attach_cohort_keys
from app.analytics.peer_anomaly.models import PeerStatistic

METRICS = [
    "critical_escalation_rate", "critical_median_investigation_minutes", "remediation_rate",
    "rapid_closure_rate", "alert_count", "case_count", "alerts_per_asset", "cases_per_asset",
    "monitoring_coverage_rate", "repeat_alert_event_rate",
]


def peer_statistics(entity_features: pl.DataFrame, metric: str, minimum_cohort_size: int = MIN_COHORT_SIZE) -> pl.DataFrame:
    """Calculate robust cohort statistics for one metric."""
    frame = attach_cohort_keys(entity_features).filter(pl.col(metric).is_not_null())
    return frame.group_by("cohort_key").agg([
        pl.len().alias("peer_count"), pl.col(metric).median().alias("peer_median"),
        pl.col(metric).mean().alias("peer_mean"), pl.col(metric).std(ddof=0).fill_null(0).alias("peer_std"),
        pl.col(metric).quantile(0.25).alias("peer_p25"), pl.col(metric).quantile(0.75).alias("peer_p75"),
    ]).filter(pl.col("peer_count") >= minimum_cohort_size).with_columns(pl.lit(metric).alias("metric_name"))


def benchmark_table(entity_features: pl.DataFrame, metrics: list[str] = METRICS) -> pl.DataFrame:
    tables = [peer_statistics(entity_features, metric) for metric in metrics if metric in entity_features.columns]
    return pl.concat(tables, how="vertical") if tables else pl.DataFrame()
