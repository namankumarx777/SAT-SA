from __future__ import annotations

import polars as pl


def build_asset_features(assets: pl.DataFrame, alerts: pl.DataFrame, cases: pl.DataFrame) -> pl.DataFrame:
    """Build one row per asset; missing activity remains explicit as zero/null."""
    reference_time = alerts["timestamp"].max()
    alert_activity = alerts.group_by("asset_id").agg([
        pl.len().alias("alert_count"),
        pl.col("case_id").is_not_null().sum().alias("case_count"),
        pl.col("timestamp").max().alias("last_alert_at"),
    ])
    result = assets.join(alert_activity, left_on="id", right_on="asset_id", how="left").with_columns([
        pl.col("alert_count").fill_null(0).cast(pl.Int64),
        pl.col("case_count").fill_null(0).cast(pl.Int64),
    ]).with_columns([
        (pl.col("alert_count") > 0).alias("has_alert_activity"),
        (pl.col("case_count") > 0).alias("has_case_activity"),
        (pl.col("expected_monitoring") & (pl.col("alert_count") == 0)).alias("expected_monitoring_no_activity"),
        pl.when(pl.col("last_alert_at").is_not_null())
        .then((pl.lit(reference_time) - pl.col("last_alert_at")).dt.total_days().cast(pl.Float64))
        .otherwise(None)
        .alias("days_since_last_alert"),
    ])
    entity_counts = result.group_by("entity_id").agg(pl.col("alert_count").sum().alias("entity_alert_count"))
    return result.join(entity_counts, on="entity_id", how="left").with_columns(
        pl.when(pl.col("entity_alert_count") > 0)
        .then(pl.col("alert_count").cast(pl.Float64) / pl.col("entity_alert_count"))
        .otherwise(None)
        .alias("asset_alert_rate_relative_to_entity")
    ).drop("entity_alert_count")
