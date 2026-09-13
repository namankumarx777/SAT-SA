from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import polars as pl

from app.ingestion.models import (
    CATEGORY_VALUES,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    QualityIssue,
)

ALIASES: dict[str, dict[str, str]] = {
    "entities": {
        "entity_id": "id",
        "entity_name": "name",
        "organization": "name",
    },
    "assets": {
        "asset_id": "id",
    },
    "alerts": {
        "alert_id": "id",
        "detected_at": "timestamp",
        "alert_time": "timestamp",
        "severity_level": "severity",
    },
    "cases": {
        "case_id": "id",
        "investigation_notes": "investigation_text",
        "escalated_flag": "escalated",
    },
    "escalations": {
        "escalation_id": "id",
    },
}

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
TEXT_FIELDS = {
    "entities": {"id", "name", "sector", "size", "criticality", "created_at"},
    "assets": {"id", "entity_id", "asset_type", "criticality", "monitoring_source"},
    "alerts": {"id", "entity_id", "asset_id", "severity", "source", "status", "case_id"},
    "cases": {"id", "entity_id", "alert_id", "investigation_text", "disposition"},
    "escalations": {"id", "entity_id", "case_id", "escalation_type"},
}


@dataclass
class NormalizationResult:
    frame: pl.DataFrame
    issues: list[QualityIssue]


def _issue(dataset: str, error_type: str, message: str, *, field: str | None = None, row: int | None = None, warning: bool = False) -> QualityIssue:
    return QualityIssue(
        dataset=dataset,
        row=row,
        field=field,
        error_type=error_type,
        message=message,
        severity="warning" if warning else "error",
    )


def _rename_aliases(frame: pl.DataFrame, dataset: str, issues: list[QualityIssue]) -> pl.DataFrame:
    rename: dict[str, str] = {}
    for alias, canonical in ALIASES.get(dataset, {}).items():
        if alias in frame.columns and canonical in frame.columns:
            issues.append(_issue(dataset, "AMBIGUOUS_ALIAS", f"Both {alias} and {canonical} are present", field=canonical))
        elif alias in frame.columns:
            rename[alias] = canonical
    return frame.rename(rename)


def _add_missing_columns(frame: pl.DataFrame, dataset: str, issues: list[QualityIssue]) -> pl.DataFrame:
    for field in REQUIRED_COLUMNS[dataset]:
        if field not in frame.columns:
            issues.append(_issue(dataset, "MISSING_REQUIRED_COLUMN", f"Required column is missing: {field}", field=field))
            frame = frame.with_columns(pl.lit(None).alias(field))
    for field in OPTIONAL_COLUMNS[dataset]:
        if field not in frame.columns:
            issues.append(_issue(dataset, "MISSING_OPTIONAL_COLUMN", f"Optional column is missing: {field}", field=field, warning=True))
            frame = frame.with_columns(pl.lit(None).alias(field))
    return frame


def _normalize_datetimes(frame: pl.DataFrame, dataset: str, issues: list[QualityIssue]) -> pl.DataFrame:
    for field in DATETIME_FIELDS[dataset]:
        if field not in frame.columns:
            continue
        if frame.schema[field] == pl.Datetime:
            continue
        source = frame[field]
        non_null = source.is_not_null().sum()
        normalized_source = source.cast(pl.String).str.replace("T", " ").str.strip_chars_end("Z")
        parsed = normalized_source.str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S%.f", strict=False)
        parsed = parsed.fill_null(normalized_source.str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False))
        parsed = parsed.fill_null(normalized_source.str.strptime(pl.Datetime, "%Y-%m-%d", strict=False))
        invalid = int(non_null - parsed.is_not_null().sum())
        if invalid:
            issues.append(_issue(dataset, "INVALID_TIMESTAMP", f"{invalid} value(s) in {field} are not parseable timestamps", field=field))
        frame = frame.with_columns(parsed.alias(field))
    return frame


def _normalize_booleans(frame: pl.DataFrame, dataset: str, issues: list[QualityIssue]) -> pl.DataFrame:
    for field in BOOLEAN_FIELDS[dataset]:
        if field not in frame.columns or frame.schema[field] == pl.Boolean:
            continue
        source = frame[field]
        normalized = source.cast(pl.String).str.strip_chars().str.to_lowercase()
        valid_values = {"true", "1", "yes", "y", "t", "false", "0", "no", "n", "f"}
        invalid = int(source.is_not_null().sum() - normalized.is_in(list(valid_values)).sum())
        if invalid:
            issues.append(_issue(dataset, "INVALID_BOOLEAN", f"{invalid} value(s) in {field} are not valid booleans", field=field))
        frame = frame.with_columns(
            pl.when(normalized.is_in(["true", "1", "yes", "y", "t"]))
            .then(pl.lit(True))
            .when(normalized.is_in(["false", "0", "no", "n", "f"]))
            .then(pl.lit(False))
            .otherwise(pl.lit(None, dtype=pl.Boolean))
            .alias(field)
        )
    return frame


def _normalize_text(frame: pl.DataFrame, dataset: str) -> pl.DataFrame:
    expressions = []
    for field in TEXT_FIELDS[dataset]:
        if field in frame.columns and frame.schema[field] == pl.String:
            expressions.append(pl.col(field).str.strip_chars().alias(field))
    return frame.with_columns(expressions) if expressions else frame


def normalize_frame(frame: pl.DataFrame, dataset: str) -> NormalizationResult:
    """Map a source frame into the canonical column contract without silent coercion."""
    if dataset not in REQUIRED_COLUMNS:
        raise ValueError(f"Unsupported dataset type: {dataset}")
    issues: list[QualityIssue] = []
    if len(frame.columns) != len(set(frame.columns)):
        issues.append(_issue(dataset, "DUPLICATE_COLUMN", "Input contains duplicate column names"))
    frame = _rename_aliases(frame, dataset, issues)
    known = set(REQUIRED_COLUMNS[dataset]) | set(OPTIONAL_COLUMNS[dataset])
    for column in frame.columns:
        if column not in known and column not in ALIASES.get(dataset, {}):
            issues.append(_issue(dataset, "UNKNOWN_COLUMN", f"Unknown column retained but ignored: {column}", field=column, warning=True))
    frame = _add_missing_columns(frame, dataset, issues)
    frame = _normalize_text(frame, dataset)
    frame = _normalize_booleans(frame, dataset, issues)
    frame = _normalize_datetimes(frame, dataset, issues)
    ordered = list(REQUIRED_COLUMNS[dataset]) + list(OPTIONAL_COLUMNS[dataset])
    return NormalizationResult(frame.select([column for column in ordered if column in frame.columns]), issues)
