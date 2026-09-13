from __future__ import annotations

import polars as pl


def _duration_minutes(end: pl.Expr, start: pl.Expr) -> pl.Expr:
    return (end - start).dt.total_minutes().cast(pl.Float64)


def build_case_features(cases: pl.DataFrame, escalations: pl.DataFrame) -> pl.DataFrame:
    """Build one deterministic feature row per canonical case."""
    escalation_times = escalations.group_by("case_id").agg(pl.col("created_at").min().alias("escalated_at"))
    return (
        cases.join(escalation_times, left_on="id", right_on="case_id", how="left")
        .with_columns([
            pl.when(pl.col("closed_at").is_not_null()).then(_duration_minutes(pl.col("closed_at"), pl.col("opened_at"))).otherwise(None).alias("investigation_minutes"),
            pl.when(pl.col("closed_at").is_not_null()).then(_duration_minutes(pl.col("closed_at"), pl.col("opened_at"))).otherwise(None).alias("case_age_at_close_minutes"),
            pl.col("closed_at").is_not_null().alias("is_closed"),
            pl.when(pl.col("escalated_at").is_not_null()).then(_duration_minutes(pl.col("escalated_at"), pl.col("opened_at"))).otherwise(None).alias("escalation_delay_minutes"),
            pl.col("escalated").cast(pl.Boolean).alias("is_escalated"),
            pl.col("remediation_recorded").cast(pl.Boolean).alias("is_remediated"),
            pl.col("investigation_text").fill_null("").str.len_chars().cast(pl.Int64).alias("investigation_text_length"),
            pl.col("investigation_text").fill_null("").str.split(by=" ").list.eval(pl.element().filter(pl.element() != "")).list.len().cast(pl.Int64).alias("investigation_word_count"),
            (pl.col("investigation_text").is_not_null() & (pl.col("investigation_text").str.len_chars() > 0)).alias("has_investigation_text"),
        ])
        .drop("escalated_at")
    )
