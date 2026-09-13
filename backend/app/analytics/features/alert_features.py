from __future__ import annotations

import polars as pl

from app.analytics.features.schemas import RECENT_ALERT_WINDOW_DAYS

SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def _duration_minutes(end: pl.Expr, start: pl.Expr) -> pl.Expr:
    return (end - start).dt.total_minutes().cast(pl.Float64)


def _recent_alert_counts(alerts: pl.DataFrame) -> pl.DataFrame:
    timestamps = alerts.select(["id", "asset_id", "timestamp"])
    pairs = alerts.select(["id", "asset_id", "timestamp"]).join(
        timestamps.rename({"id": "other_id", "timestamp": "other_timestamp"}),
        on="asset_id",
        how="left",
    )
    recent = pairs.filter(
        (pl.col("other_timestamp") <= pl.col("timestamp"))
        & (pl.col("other_timestamp") >= pl.col("timestamp") - pl.duration(days=RECENT_ALERT_WINDOW_DAYS))
    ).group_by("id").len().rename({"len": "asset_recent_alert_count"})
    return recent


def build_alert_features(alerts: pl.DataFrame) -> pl.DataFrame:
    """Build one deterministic feature row per canonical alert."""
    counts = alerts.group_by("asset_id").agg([
        pl.len().alias("asset_alert_count"),
        pl.col("source").n_unique().alias("asset_distinct_alert_sources"),
    ])
    recent = _recent_alert_counts(alerts)
    return (
        alerts.join(counts, on="asset_id", how="left")
        .join(recent, on="id", how="left")
        .with_columns([
            pl.when(pl.col("acknowledged_at").is_not_null()).then(_duration_minutes(pl.col("acknowledged_at"), pl.col("timestamp"))).otherwise(None).alias("acknowledgement_minutes"),
            pl.when(pl.col("closed_at").is_not_null()).then(_duration_minutes(pl.col("closed_at"), pl.col("timestamp"))).otherwise(None).alias("alert_lifetime_minutes"),
            pl.col("case_id").is_not_null().alias("has_case"),
            (pl.col("status").eq("Closed") | pl.col("closed_at").is_not_null()).alias("is_closed"),
            pl.col("severity").replace_strict(SEVERITY_RANK, default=None).cast(pl.Int64).alias("severity_rank"),
            pl.col("severity").is_in(["High", "Critical"]).alias("is_high_or_critical"),
            pl.col("severity").eq("Critical").alias("is_critical"),
            pl.col("asset_recent_alert_count").fill_null(0).cast(pl.Int64),
        ])
    )
