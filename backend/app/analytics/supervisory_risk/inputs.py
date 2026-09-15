from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class StandardizedFinding:
    id: str
    rule_id: str
    entity_id: str
    source_phase: str
    finding_type: str
    severity: str
    confidence: str
    evidence_strength: str | None
    confidence_type: str | None
    title: str
    summary: str
    rationale: str
    status: str
    created_at: str
    metric_name: str | None = None
    observed_value: float | int | str | None = None
    expected_value: float | int | str | None = None
    threshold: float | int | str | None = None
    population_size: int | None = None
    absolute_gap: float | None = None
    relative_gap: float | None = None
    baseline_method: str | None = None
    baseline_type: str | None = None
    baseline_value: float | None = None
    reference_value: float | None = None
    gap_value: float | None = None
    gap_direction: str | None = None
    anomaly_score: float | None = None
    anomaly_rank: int | None = None
    contributing_deviations: list[dict[str, Any]] | None = None


@dataclass
class StandardizedEvidence:
    id: str
    finding_id: str
    source_type: str
    source_id: str
    entity_id: str
    field: str
    value: Any
    reason: str


@dataclass
class UpstreamBundle:
    entities: dict[str, dict[str, Any]]
    findings: list[StandardizedFinding]
    evidence_by_finding: dict[str, list[StandardizedEvidence]]
    phase_counts: dict[str, int]
    source_paths: dict[str, str]


def _format_timestamp(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


def _parse_json_list(val: Any) -> list[dict[str, Any]] | None:
    if val is None:
        return None
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return None
    return None


def _find_phase_dir(root: Path, prefixes: list[str]) -> Path:
    for prefix in prefixes:
        candidate = root / prefix
        if candidate.is_dir() and (candidate / "findings.parquet").is_file():
            return candidate
        # Also check root directly if root is already the phase dir
        if root.name.startswith(prefix) and (root / "findings.parquet").is_file():
            return root
    # Check if files are directly inside root
    if (root / "findings.parquet").is_file():
        return root
    raise FileNotFoundError(f"Could not locate findings for prefixes {prefixes} in {root}")


def _load_phase_findings(
    phase_dir: Path, source_phase: str
) -> tuple[list[StandardizedFinding], list[StandardizedEvidence]]:
    findings_path = phase_dir / "findings.parquet"
    evidence_path = phase_dir / "evidence.parquet"

    if not findings_path.is_file():
        return [], []

    df_findings = pl.read_parquet(findings_path)
    findings: list[StandardizedFinding] = []

    for row in df_findings.to_dicts():
        contributions = _parse_json_list(row.get("contributing_deviations"))
        finding = StandardizedFinding(
            id=str(row["id"]),
            rule_id=str(row["rule_id"]),
            entity_id=str(row["entity_id"]),
            source_phase=source_phase,
            finding_type=str(row["finding_type"]),
            severity=str(row["severity"]),
            confidence=str(row.get("confidence", "Medium")),
            evidence_strength=row.get("evidence_strength") if row.get("evidence_strength") is not None else None,
            confidence_type=row.get("confidence_type"),
            title=str(row.get("title", "")),
            summary=str(row.get("summary", "")),
            rationale=str(row.get("rationale", "")),
            status=str(row.get("status", "OPEN")),
            created_at=_format_timestamp(row.get("created_at")),
            metric_name=row.get("metric_name"),
            observed_value=row.get("observed_value"),
            expected_value=row.get("expected_value"),
            threshold=row.get("threshold"),
            population_size=row.get("population_size"),
            absolute_gap=row.get("absolute_gap"),
            relative_gap=row.get("relative_gap"),
            baseline_method=row.get("baseline_method"),
            baseline_type=row.get("baseline_type"),
            baseline_value=row.get("baseline_value"),
            reference_value=row.get("reference_value"),
            gap_value=row.get("gap_value"),
            gap_direction=row.get("gap_direction"),
            anomaly_score=row.get("anomaly_score"),
            anomaly_rank=row.get("anomaly_rank"),
            contributing_deviations=contributions,
        )
        findings.append(finding)

    evidence_list: list[StandardizedEvidence] = []
    if evidence_path.is_file():
        df_evidence = pl.read_parquet(evidence_path)
        for row in df_evidence.to_dicts():
            evidence = StandardizedEvidence(
                id=str(row["id"]),
                finding_id=str(row["finding_id"]),
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                entity_id=str(row["entity_id"]),
                field=str(row["field"]),
                value=row.get("value"),
                reason=str(row.get("reason", "")),
            )
            evidence_list.append(evidence)

    return findings, evidence_list


def load_upstream_bundle(
    root_dir: str | Path,
    phase4_dir: str | Path | None = None,
    phase5_dir: str | Path | None = None,
    phase6_dir: str | Path | None = None,
    phase7_dir: str | Path | None = None,
    phase8_dir: str | Path | None = None,
) -> UpstreamBundle:
    """Load and harmonize outputs across Phases 4, 5, 6, 7, and 8."""
    root = Path(root_dir)

    # 1. Phase 4 Entity Features (Denominators & Metadata)
    if phase4_dir:
        p4_path = Path(phase4_dir) / "entity_features.parquet"
    else:
        candidates = [
            root / "phase4-final" / "entity_features.parquet",
            root / "phase4-features" / "entity_features.parquet",
            root / "phase4-check" / "entity_features.parquet",
            root / "entity_features.parquet",
        ]
        p4_path = next((p for p in candidates if p.is_file()), None)
        if p4_path is None:
            raise FileNotFoundError(f"Cannot find entity_features.parquet in {root}")

    df_entities = pl.read_parquet(p4_path)
    entities_map: dict[str, dict[str, Any]] = {
        row["entity_id"]: row for row in df_entities.to_dicts()
    }

    # 2. Phase 5, 6, 7, 8 Findings & Evidence
    phase_configs = [
        ("phase5", phase5_dir, ["phase5-final", "phase5-findings", "phase5-final-a"]),
        ("phase6", phase6_dir, ["execution_gap-final", "execution_gap"]),
        ("phase7", phase7_dir, ["negative_space-final", "negative_space"]),
        ("phase8", phase8_dir, ["peer_anomaly-final", "peer_anomaly"]),
    ]

    all_findings: list[StandardizedFinding] = []
    evidence_by_finding: dict[str, list[StandardizedEvidence]] = {}
    phase_counts: dict[str, int] = {}
    source_paths: dict[str, str] = {"phase4": str(p4_path)}

    for phase_name, explicit_dir, prefix_candidates in phase_configs:
        if explicit_dir:
            p_dir = Path(explicit_dir)
        else:
            try:
                p_dir = _find_phase_dir(root, prefix_candidates)
            except FileNotFoundError:
                p_dir = None

        if p_dir is not None and p_dir.is_dir():
            findings, evidence = _load_phase_findings(p_dir, phase_name)
            all_findings.extend(findings)
            for ev in evidence:
                evidence_by_finding.setdefault(ev.finding_id, []).append(ev)
            phase_counts[phase_name] = len(findings)
            source_paths[phase_name] = str(p_dir)
        else:
            phase_counts[phase_name] = 0
            source_paths[phase_name] = "NOT_FOUND"

    return UpstreamBundle(
        entities=entities_map,
        findings=all_findings,
        evidence_by_finding=evidence_by_finding,
        phase_counts=phase_counts,
        source_paths=source_paths,
    )
