from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from app.analytics.rules.definitions import RULES, enabled_rules
from app.analytics.rules.evaluators import EVALUATORS
from app.analytics.rules.models import Evidence, Finding, RuleDefinition, RuleRunResult

FEATURE_TABLES = ("alert_features", "case_features", "asset_features", "entity_features", "entity_month_features")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "phase5-findings"


def load_feature_bundle(input_dir: str | Path) -> dict[str, pl.DataFrame]:
    """Load all required Phase 4 feature tables from a feature output directory."""
    directory = Path(input_dir)
    if not directory.is_dir():
        raise ValueError(f"Feature input directory not found: {directory}")
    bundle: dict[str, pl.DataFrame] = {}
    missing: list[str] = []
    for name in FEATURE_TABLES:
        path = directory / f"{name}.parquet"
        if not path.is_file():
            missing.append(name)
        else:
            bundle[name] = pl.read_parquet(path)
    if missing:
        raise ValueError(f"Feature dataset is missing: {', '.join(missing)}")
    return bundle


def evaluate_rule(rule: RuleDefinition, feature_bundle: dict[str, pl.DataFrame]) -> tuple[list[Finding], list[Evidence]]:
    """Evaluate one enabled rule through its isolated deterministic evaluator."""
    if not rule.enabled:
        return [], []
    evaluator = EVALUATORS.get(rule.rule_id)
    if evaluator is None:
        raise ValueError(f"No evaluator registered for {rule.rule_id}")
    return evaluator(rule, feature_bundle)


def evaluate_all_rules(feature_bundle: dict[str, pl.DataFrame]) -> RuleRunResult:
    """Evaluate all enabled rules and return stable, duplicate-free outputs."""
    findings: list[Finding] = []
    evidence: list[Evidence] = []
    evaluated: list[str] = []
    for rule in enabled_rules():
        rule_findings, rule_evidence = evaluate_rule(rule, feature_bundle)
        evaluated.append(rule.rule_id)
        findings.extend(rule_findings)
        evidence.extend(rule_evidence)
    unique_findings = {finding.id: finding for finding in findings}
    unique_evidence = {item.id: item for item in evidence}
    ordered_findings = sorted(unique_findings.values(), key=lambda item: (item.rule_id, item.entity_id, item.id))
    ordered_evidence = sorted(unique_evidence.values(), key=lambda item: (item.finding_id, item.source_type, item.source_id, item.field, item.id))
    finding_ids = {finding.id for finding in ordered_findings}
    ordered_evidence = [item for item in ordered_evidence if item.finding_id in finding_ids]
    return RuleRunResult(findings=ordered_findings, evidence=ordered_evidence, rules_evaluated=evaluated)


def _findings_frame(findings: list[Finding]) -> pl.DataFrame:
    if not findings:
        return pl.DataFrame(schema={
            "id": pl.String, "rule_id": pl.String, "entity_id": pl.String, "finding_type": pl.String,
            "severity": pl.String, "confidence": pl.String, "title": pl.String, "summary": pl.String,
            "rationale": pl.String, "status": pl.String, "created_at": pl.Datetime,
            "metric_name": pl.String, "observed_value": pl.Float64, "expected_value": pl.Float64,
            "threshold": pl.Float64, "population_size": pl.Int64,
        })
    return pl.DataFrame([finding.model_dump() for finding in findings]).sort(["rule_id", "entity_id", "id"])


def _evidence_frame(evidence: list[Evidence]) -> pl.DataFrame:
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


def write_rule_outputs(result: RuleRunResult, output_dir: str | Path, dataset_id: str) -> dict[str, object]:
    """Write deterministic findings/evidence Parquet and a rule manifest."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _findings_frame(result.findings).write_parquet(destination / "findings.parquet")
    _evidence_frame(result.evidence).write_parquet(destination / "evidence.parquet")
    manifest = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules": [rule.model_dump() for rule in enabled_rules()],
        "rules_evaluated": result.rules_evaluated,
        "thresholds": {rule.rule_id: rule.thresholds for rule in enabled_rules()},
        "row_counts": {"findings": len(result.findings), "evidence": len(result.evidence)},
    }
    (destination / "rule_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_rules(input_dir: str | Path, output_dir: str | Path = DEFAULT_OUTPUT, dataset_id: str | None = None) -> RuleRunResult:
    """Load Phase 4 features, evaluate rules, and write outputs."""
    source = Path(input_dir)
    result = evaluate_all_rules(load_feature_bundle(source))
    write_rule_outputs(result, output_dir, dataset_id or source.name)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAT-SA deterministic supervisory rules.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dataset-id")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_rules(args.input, args.output, args.dataset_id)
    print(f"Rules evaluated: {', '.join(result.rules_evaluated)}")
    print(f"Findings: {len(result.findings)}")
    print(f"By rule: {dict(Counter(item.rule_id for item in result.findings))}")
    print(f"By severity: {dict(Counter(item.severity for item in result.findings))}")
    print(f"Evidence: {len(result.evidence)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
