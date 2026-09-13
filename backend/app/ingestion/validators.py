from __future__ import annotations

import polars as pl

from app.ingestion.models import CATEGORY_VALUES, REQUIRED_COLUMNS, QualityIssue

DATETIME_FIELDS = {
    "entities": {"created_at"},
    "assets": set(),
    "alerts": {"timestamp", "acknowledged_at", "closed_at"},
    "cases": {"opened_at", "closed_at"},
    "escalations": {"created_at"},
}
BOOLEAN_FIELDS = {
    "entities": set(),
    "assets": {"expected_monitoring"},
    "alerts": set(),
    "cases": {"escalated", "remediation_recorded"},
    "escalations": set(),
}
ID_FIELDS = {
    "entities": {"id"},
    "assets": {"id", "entity_id"},
    "alerts": {"id", "entity_id", "asset_id"},
    "cases": {"id", "entity_id", "alert_id"},
    "escalations": {"id", "entity_id", "case_id"},
}


def _error(dataset: str, error_type: str, message: str, *, field: str | None = None) -> QualityIssue:
    return QualityIssue(dataset=dataset, field=field, error_type=error_type, message=message)


def _count_issue(dataset: str, error_type: str, frame: pl.DataFrame, message: str, *, field: str | None = None) -> QualityIssue | None:
    count = frame.height
    if count == 0:
        return None
    return _error(dataset, error_type, message.format(count=count), field=field)


def validate_frame(frame: pl.DataFrame, dataset: str) -> list[QualityIssue]:
    """Validate nullability, types, uniqueness, and categorical values for one table."""
    issues: list[QualityIssue] = []
    for field in REQUIRED_COLUMNS[dataset]:
        if field not in frame.columns:
            continue
        nulls = frame[field].null_count()
        if nulls:
            issues.append(_error(dataset, "REQUIRED_NULL", f"{nulls} null value(s) in required field {field}", field=field))
    for field in ID_FIELDS[dataset]:
        if field in frame.columns and frame.schema[field] != pl.String:
            issues.append(_error(dataset, "INVALID_TYPE", f"Field {field} must contain strings", field=field))
    for field in BOOLEAN_FIELDS[dataset]:
        if field in frame.columns and frame.schema[field] != pl.Boolean:
            issues.append(_error(dataset, "INVALID_TYPE", f"Field {field} must contain booleans", field=field))
    for field in DATETIME_FIELDS[dataset]:
        if field in frame.columns and frame[field].dtype not in (pl.Datetime, pl.Null):
            issues.append(_error(dataset, "INVALID_TYPE", f"Field {field} must contain datetimes", field=field))
    if "id" in frame.columns and frame["id"].n_unique() != frame.height:
        issues.append(_error(dataset, "DUPLICATE_ID", f"{frame.height - frame['id'].n_unique()} duplicate {dataset} ID value(s)", field="id"))
    for field, allowed in CATEGORY_VALUES.items():
        if field not in frame.columns:
            continue
        invalid = frame.filter(pl.col(field).is_not_null() & ~pl.col(field).is_in(list(allowed)))
        if invalid.height:
            values = invalid[field].unique().to_list()[:5]
            issues.append(_error(dataset, "INVALID_CATEGORY", f"Unknown {field} value(s): {values}", field=field))
    return issues


def validate_references(bundle: dict[str, pl.DataFrame]) -> list[QualityIssue]:
    """Validate foreign keys when the referenced tables are available."""
    issues: list[QualityIssue] = []
    if "entities" in bundle:
        entities = bundle["entities"].select("id").unique()
        for dataset in ("assets", "alerts", "cases", "escalations"):
            if dataset in bundle:
                frame = bundle[dataset]
                orphan = frame.join(entities, left_on="entity_id", right_on="id", how="anti")
                issue = _count_issue(dataset, "ORPHAN_ENTITY", orphan, "{count} row(s) reference unknown entity IDs", field="entity_id")
                if issue:
                    issues.append(issue)
    if "assets" in bundle and "alerts" in bundle:
        assets = bundle["assets"].select(["id", "entity_id"])
        alerts = bundle["alerts"].join(assets, left_on="asset_id", right_on="id", how="left", suffix="_asset")
        missing = alerts.filter(pl.col("entity_id_asset").is_null())
        issue = _count_issue("alerts", "ORPHAN_ASSET", missing, "{count} alert(s) reference unknown asset IDs", field="asset_id")
        if issue:
            issues.append(issue)
        mismatch = alerts.filter(pl.col("entity_id_asset").is_not_null() & (pl.col("entity_id") != pl.col("entity_id_asset")))
        issue = _count_issue("alerts", "ENTITY_MISMATCH", mismatch, "{count} alert(s) reference assets owned by another entity", field="asset_id")
        if issue:
            issues.append(issue)
    if "alerts" in bundle and "cases" in bundle:
        alerts = bundle["alerts"].select(["id", "entity_id"])
        cases = bundle["cases"].join(alerts, left_on="alert_id", right_on="id", how="left", suffix="_alert")
        missing = cases.filter(pl.col("entity_id_alert").is_null())
        issue = _count_issue("cases", "ORPHAN_ALERT", missing, "{count} case(s) reference unknown alert IDs", field="alert_id")
        if issue:
            issues.append(issue)
        mismatch = cases.filter(pl.col("entity_id_alert").is_not_null() & (pl.col("entity_id") != pl.col("entity_id_alert")))
        issue = _count_issue("cases", "ENTITY_MISMATCH", mismatch, "{count} case(s) reference alerts owned by another entity", field="alert_id")
        if issue:
            issues.append(issue)
    if "cases" in bundle and "escalations" in bundle:
        cases = bundle["cases"].select(["id", "entity_id"])
        escalations = bundle["escalations"].join(cases, left_on="case_id", right_on="id", how="left", suffix="_case")
        missing = escalations.filter(pl.col("entity_id_case").is_null())
        issue = _count_issue("escalations", "ORPHAN_CASE", missing, "{count} escalation(s) reference unknown case IDs", field="case_id")
        if issue:
            issues.append(issue)
        mismatch = escalations.filter(pl.col("entity_id_case").is_not_null() & (pl.col("entity_id") != pl.col("entity_id_case")))
        issue = _count_issue("escalations", "ENTITY_MISMATCH", mismatch, "{count} escalation(s) reference cases owned by another entity", field="case_id")
        if issue:
            issues.append(issue)
    return issues


def validate_temporal(bundle: dict[str, pl.DataFrame]) -> list[QualityIssue]:
    """Validate nullable lifecycle ordering using Polars joins."""
    issues: list[QualityIssue] = []
    alerts = bundle.get("alerts")
    if alerts is not None:
        issue = _count_issue("alerts", "IMPOSSIBLE_TIMESTAMP", alerts.filter(pl.col("acknowledged_at").is_not_null() & (pl.col("acknowledged_at") < pl.col("timestamp"))), "{count} acknowledgement timestamp(s) precede the alert", field="acknowledged_at")
        if issue:
            issues.append(issue)
        issue = _count_issue("alerts", "IMPOSSIBLE_TIMESTAMP", alerts.filter(pl.col("closed_at").is_not_null() & (pl.col("closed_at") < pl.col("timestamp"))), "{count} closure timestamp(s) precede the alert", field="closed_at")
        if issue:
            issues.append(issue)
        issue = _count_issue("alerts", "IMPOSSIBLE_TIMESTAMP", alerts.filter(pl.col("closed_at").is_not_null() & pl.col("acknowledged_at").is_not_null() & (pl.col("closed_at") < pl.col("acknowledged_at"))), "{count} closure timestamp(s) precede acknowledgement", field="closed_at")
        if issue:
            issues.append(issue)
    cases = bundle.get("cases")
    if cases is not None:
        issue = _count_issue("cases", "IMPOSSIBLE_TIMESTAMP", cases.filter(pl.col("closed_at").is_not_null() & (pl.col("closed_at") < pl.col("opened_at"))), "{count} case closure timestamp(s) precede opening", field="closed_at")
        if issue:
            issues.append(issue)
        if alerts is not None:
            joined = cases.join(alerts.select(["id", "timestamp", "acknowledged_at"]), left_on="alert_id", right_on="id", how="inner", suffix="_alert")
            issue = _count_issue("cases", "IMPOSSIBLE_TIMESTAMP", joined.filter(pl.col("opened_at") < pl.col("timestamp")), "{count} case(s) open before their alert", field="opened_at")
            if issue:
                issues.append(issue)
            issue = _count_issue("cases", "IMPOSSIBLE_TIMESTAMP", joined.filter(pl.col("acknowledged_at").is_not_null() & (pl.col("opened_at") < pl.col("acknowledged_at"))), "{count} case(s) open before acknowledgement", field="opened_at")
            if issue:
                issues.append(issue)
    escalations = bundle.get("escalations")
    if escalations is not None and cases is not None:
        joined = escalations.join(cases.select(["id", "opened_at", "closed_at"]), left_on="case_id", right_on="id", how="inner", suffix="_case")
        issue = _count_issue("escalations", "IMPOSSIBLE_TIMESTAMP", joined.filter(pl.col("created_at") < pl.col("opened_at")), "{count} escalation(s) precede case opening", field="created_at")
        if issue:
            issues.append(issue)
        issue = _count_issue("escalations", "IMPOSSIBLE_TIMESTAMP", joined.filter(pl.col("closed_at").is_not_null() & (pl.col("created_at") > pl.col("closed_at"))), "{count} escalation(s) occur after case closure", field="created_at")
        if issue:
            issues.append(issue)
    return issues


def validate_bundle(bundle: dict[str, pl.DataFrame]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for dataset, frame in bundle.items():
        issues.extend(validate_frame(frame, dataset))
    issues.extend(validate_references(bundle))
    issues.extend(validate_temporal(bundle))
    return issues
