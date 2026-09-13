from __future__ import annotations

import polars as pl

from app.analytics.features.schemas import RAPID_CLOSURE_MINUTES


def _safe_rate(numerator: pl.Expr, denominator: pl.Expr) -> pl.Expr:
    return pl.when(denominator > 0).then(numerator.cast(pl.Float64) / denominator).otherwise(None)


def build_entity_features(entities: pl.DataFrame, alerts: pl.DataFrame, cases: pl.DataFrame, assets: pl.DataFrame) -> pl.DataFrame:
    """Build one operational feature row per entity, preserving zero-activity entities."""
    alert_metrics = alerts.group_by("entity_id").agg([
        pl.len().alias("alert_count"),
        (pl.col("case_id").is_not_null()).sum().alias("alerts_with_cases"),
        (~pl.col("is_closed")).sum().alias("open_alert_count"),
        pl.col("is_closed").sum().alias("closed_alert_count"),
        (pl.col("severity") == "Low").sum().alias("low_alert_count"),
        (pl.col("severity") == "Medium").sum().alias("medium_alert_count"),
        (pl.col("severity") == "High").sum().alias("high_alert_count"),
        (pl.col("severity") == "Critical").sum().alias("critical_alert_count"),
        pl.col("is_critical").mean().alias("critical_alert_rate"),
        pl.col("is_high_or_critical").mean().alias("high_critical_alert_rate"),
        pl.col("asset_alert_count").gt(1).sum().alias("repeat_alert_event_count"),
    ])
    case_metrics = cases.group_by("entity_id").agg([
        pl.len().alias("case_count"),
        pl.col("is_closed").sum().alias("closed_case_count"),
        pl.col("is_escalated").sum().alias("escalated_case_count"),
        (~pl.col("is_escalated")).sum().alias("non_escalated_case_count"),
        (pl.col("is_escalated") & (pl.col("severity") == "Critical")).sum().alias("critical_escalated_case_count"),
        (pl.col("severity") == "Critical").sum().alias("critical_case_count"),
        pl.when(pl.col("severity") == "Critical").then(pl.col("is_closed")).otherwise(False).sum().alias("critical_closed_case_count"),
        pl.when(pl.col("severity") == "Critical").then(pl.col("investigation_minutes")).otherwise(None).mean().alias("critical_mean_investigation_minutes"),
        pl.when(pl.col("severity") == "Critical").then(pl.col("investigation_minutes")).otherwise(None).median().alias("critical_median_investigation_minutes"),
        (pl.col("is_remediated") & pl.col("is_closed")).sum().alias("remediated_case_count"),
        ((~pl.col("is_remediated")) & pl.col("is_closed")).sum().alias("non_remediated_case_count"),
        pl.col("investigation_minutes").mean().alias("mean_investigation_minutes"),
        pl.col("investigation_minutes").median().alias("median_investigation_minutes"),
        (pl.col("is_closed") & (pl.col("investigation_minutes") <= RAPID_CLOSURE_MINUTES)).sum().alias("rapid_closure_count"),
        ((pl.col("severity") == "Critical") & pl.col("is_closed") & (pl.col("investigation_minutes") <= RAPID_CLOSURE_MINUTES)).sum().alias("critical_rapid_closure_count"),
    ])
    asset_metrics = assets.group_by("entity_id").agg([
        pl.len().alias("total_assets"),
        pl.col("expected_monitoring").sum().alias("expected_monitored_assets"),
        (pl.col("has_alert_activity") & pl.col("expected_monitoring")).sum().alias("expected_monitored_assets_with_activity"),
        (pl.col("expected_monitoring") & ~pl.col("has_alert_activity")).sum().alias("expected_monitored_assets_without_activity"),
        pl.col("has_alert_activity").sum().alias("assets_with_alert_activity"),
        (pl.col("criticality").is_in(["High", "Critical"])).sum().alias("critical_assets"),
        ((pl.col("criticality").is_in(["High", "Critical"])) & pl.col("has_alert_activity")).sum().alias("critical_assets_with_activity"),
        (pl.col("alert_count") > 1).sum().alias("repeat_alert_asset_count"),
    ])
    result = entities.rename({"id": "entity_id"}).join(alert_metrics, on="entity_id", how="left").join(case_metrics, on="entity_id", how="left").join(asset_metrics, on="entity_id", how="left")
    count_columns = [
        "alert_count", "alerts_with_cases", "open_alert_count", "closed_alert_count",
        "low_alert_count", "medium_alert_count", "high_alert_count", "critical_alert_count",
        "repeat_alert_event_count", "case_count", "closed_case_count", "escalated_case_count",
        "non_escalated_case_count", "critical_escalated_case_count", "critical_case_count", "critical_closed_case_count",
        "remediated_case_count", "non_remediated_case_count", "rapid_closure_count", "critical_rapid_closure_count",
        "total_assets", "expected_monitored_assets", "expected_monitored_assets_with_activity",
        "expected_monitored_assets_without_activity", "assets_with_alert_activity", "critical_assets",
        "critical_assets_with_activity", "repeat_alert_asset_count",
    ]
    result = result.with_columns([pl.col(column).fill_null(0).alias(column) for column in count_columns])
    return result.with_columns([
        _safe_rate(pl.col("case_count"), pl.col("alert_count")).alias("case_rate"),
        _safe_rate(pl.col("escalated_case_count"), pl.col("case_count")).alias("escalation_rate"),
        _safe_rate(pl.col("critical_escalated_case_count"), pl.col("critical_case_count")).alias("critical_escalation_rate"),
        _safe_rate(pl.col("critical_rapid_closure_count"), pl.col("critical_closed_case_count")).alias("critical_rapid_closure_rate"),
        _safe_rate(pl.col("remediated_case_count"), pl.col("closed_case_count")).alias("remediation_rate"),
        _safe_rate(pl.col("rapid_closure_count"), pl.col("closed_case_count")).alias("rapid_closure_rate"),
        _safe_rate(pl.col("repeat_alert_event_count"), pl.col("alert_count")).alias("repeat_alert_event_rate"),
        _safe_rate(pl.col("repeat_alert_asset_count"), pl.col("assets_with_alert_activity")).alias("repeat_alert_asset_rate"),
        pl.col("assets_with_alert_activity").alias("distinct_active_assets"),
        _safe_rate(pl.col("case_count"), pl.col("total_assets")).alias("cases_per_asset"),
        _safe_rate(pl.col("alert_count"), pl.col("total_assets")).alias("alerts_per_asset"),
        _safe_rate(pl.col("expected_monitored_assets_with_activity"), pl.col("expected_monitored_assets")).alias("monitoring_coverage_rate"),
        _safe_rate(pl.col("critical_assets_with_activity"), pl.col("critical_assets")).alias("critical_asset_activity_rate"),
    ])
