"""Deterministic ordering and Parquet serialization for detector outputs.

The ordering and serialization helpers here are the single source of truth for
the stable output contract shared by every phase engine. Column order, sort
order, container encoding, and the empty-frame schema are all defined here so
Phase 5-8 outputs stay byte-stable across runs and platforms.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import polars as pl

from app.analytics.detectors.models import Evidence, Finding


def order_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Deduplicate by finding id and order stably by rule, entity, then id."""
    unique = {item.id: item for item in findings}
    return sorted(unique.values(), key=lambda item: (item.rule_id, item.entity_id, item.id))


def order_evidence(
    evidence: Iterable[Evidence],
    finding_ids: Iterable[str] | None = None,
) -> list[Evidence]:
    """Deduplicate by evidence id, optionally prune orphans, and order stably."""
    unique = {item.id: item for item in evidence}
    items: Iterable[Evidence] = unique.values()
    if finding_ids is not None:
        allowed = set(finding_ids)
        items = [item for item in items if item.finding_id in allowed]
    return sorted(items, key=lambda item: (item.finding_id, item.source_type, item.source_id, item.field, item.id))


def canonical_frame(items: list[Any]) -> pl.DataFrame:
    """Serialize pydantic finding/evidence rows into a stable Parquet frame.

    Non-scalar values are encoded deterministically: lists and dicts via
    sort-keys JSON, everything else via string form. Both non-empty and empty
    cases are handled so callers always receive a well-formed frame.
    """
    if not items:
        return pl.DataFrame()
    rows = [item.model_dump() for item in items]
    for row in rows:
        for key, value in row.items():
            if value is None or isinstance(value, (str, int, float, bool)):
                continue
            row[key] = json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else str(value)
    return pl.DataFrame(rows)


def findings_frame(findings: list[Finding]) -> pl.DataFrame:
    """Phase 5 findings frame with explicit schema and stable ordering."""
    if not findings:
        return pl.DataFrame(schema={
            "id": pl.String, "rule_id": pl.String, "entity_id": pl.String, "finding_type": pl.String,
            "severity": pl.String, "confidence": pl.String, "title": pl.String, "summary": pl.String,
            "rationale": pl.String, "status": pl.String, "created_at": pl.Datetime,
            "metric_name": pl.String, "observed_value": pl.Float64, "expected_value": pl.Float64,
            "threshold": pl.Float64, "population_size": pl.Int64,
        })
    return pl.DataFrame([finding.model_dump() for finding in findings]).sort(["rule_id", "entity_id", "id"])


def evidence_frame(evidence: list[Evidence]) -> pl.DataFrame:
    """Phase 5 evidence frame with explicit schema and stable ordering."""
    if not evidence:
        return pl.DataFrame(schema={
            "id": pl.String, "finding_id": pl.String, "source_type": pl.String, "source_id": pl.String,
            "entity_id": pl.String, "field": pl.String, "value": pl.String, "reason": pl.String,
        })
    rows = [item.model_dump() for item in evidence]
    for row in rows:
        if not isinstance(row["value"], (str, int, float, bool)) and row["value"] is not None:
            row["value"] = str(row["value"])
    return pl.DataFrame(rows).sort(["finding_id", "source_type", "source_id", "field", "id"])