from __future__ import annotations

import polars as pl


def add_time_features(frame: pl.DataFrame, timestamp_column: str) -> pl.DataFrame:
    """Add deterministic calendar fields from a canonical datetime column."""
    return frame.with_columns([
        pl.col(timestamp_column).dt.year().alias("year"),
        pl.col(timestamp_column).dt.month().alias("month"),
        pl.col(timestamp_column).dt.week().alias("week"),
        pl.col(timestamp_column).dt.weekday().alias("day_of_week"),
        pl.col(timestamp_column).dt.hour().alias("hour"),
        pl.col(timestamp_column).dt.date().alias("date"),
    ])


def build_entity_month_features(alerts: pl.DataFrame, cases: pl.DataFrame) -> pl.DataFrame:
    """Aggregate observed alert and case activity by entity and calendar month."""
    alert_months = add_time_features(alerts, "timestamp").group_by(["entity_id", "year", "month"]).agg([
        pl.len().alias("alert_count"),
        pl.col("is_critical").sum().alias("critical_alert_count"),
    ])
    case_months = add_time_features(cases, "opened_at").group_by(["entity_id", "year", "month"]).agg([
        pl.len().alias("case_count"),
        pl.col("is_escalated").sum().alias("escalated_case_count"),
        pl.col("is_closed").sum().alias("investigated_case_count"),
        pl.col("is_remediated").sum().alias("remediated_case_count"),
        pl.col("investigation_minutes").mean().alias("mean_investigation_minutes"),
        pl.col("investigation_minutes").median().alias("median_investigation_minutes"),
    ])
    return alert_months.join(case_months, on=["entity_id", "year", "month"], how="full", coalesce=True).with_columns([
        pl.col("alert_count").fill_null(0),
        pl.col("critical_alert_count").fill_null(0),
        pl.col("case_count").fill_null(0),
        pl.col("escalated_case_count").fill_null(0),
        pl.col("investigated_case_count").fill_null(0),
        pl.col("remediated_case_count").fill_null(0),
    ]).sort(["entity_id", "year", "month"])
