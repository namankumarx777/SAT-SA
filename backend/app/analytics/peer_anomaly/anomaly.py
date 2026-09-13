from __future__ import annotations

import polars as pl
from sklearn.ensemble import IsolationForest

from app.analytics.peer_anomaly.definitions import CONTAMINATION, N_ESTIMATORS, RANDOM_STATE

ANOMALY_FEATURES = [
    "alert_count", "case_count", "alerts_per_asset", "cases_per_asset", "critical_alert_rate",
    "critical_escalation_rate", "critical_median_investigation_minutes", "remediation_rate",
    "rapid_closure_rate", "monitoring_coverage_rate", "repeat_alert_event_rate",
]


def prepare_anomaly_matrix(entity_features: pl.DataFrame) -> tuple[pl.DataFrame, list[str]]:
    available = [column for column in ANOMALY_FEATURES if column in entity_features.columns]
    usable = [column for column in available if entity_features[column].null_count() / max(entity_features.height, 1) <= 0.5 and entity_features[column].n_unique() > 1]
    if not usable:
        return pl.DataFrame(), []
    matrix = entity_features.select(usable).with_columns([pl.col(column).cast(pl.Float64).fill_null(pl.col(column).median()).alias(column) for column in usable])
    return matrix, usable


def detect_anomalies(entity_features: pl.DataFrame) -> tuple[pl.DataFrame, list[str]]:
    matrix, features = prepare_anomaly_matrix(entity_features)
    if entity_features.height < 10 or not features:
        return pl.DataFrame(), features
    model = IsolationForest(n_estimators=N_ESTIMATORS, contamination=CONTAMINATION, random_state=RANDOM_STATE, n_jobs=1)
    values = matrix.to_numpy()
    labels = model.fit_predict(values)
    scores = model.decision_function(values)
    result = entity_features.select("entity_id").with_columns([
        pl.Series("model_label", labels), pl.Series("anomaly_score", scores),
    ]).with_columns(
        pl.col("anomaly_score").rank(method="ordinal", descending=False).cast(pl.Int64).alias("anomaly_rank")
    )
    return result.filter(pl.col("model_label") == -1).drop("model_label"), features
