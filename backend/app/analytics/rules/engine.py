from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from app.analytics.detectors.bundle import load_feature_bundle
from app.analytics.detectors.models import Evidence, Finding
from app.analytics.detectors.output import evidence_frame, findings_frame, order_evidence, order_findings
from app.analytics.rules.definitions import RULES, enabled_rules
from app.analytics.rules.evaluators import EVALUATORS
from app.analytics.rules.models import RuleDefinition, RuleRunResult

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "phase5-findings"


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
    ordered_findings = order_findings(findings)
    ordered_evidence = order_evidence(evidence, (item.id for item in ordered_findings))
    return RuleRunResult(findings=ordered_findings, evidence=ordered_evidence, rules_evaluated=evaluated)


def write_rule_outputs(result: RuleRunResult, output_dir: str | Path, dataset_id: str) -> dict[str, object]:
    """Write deterministic findings/evidence Parquet and a rule manifest."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    findings_frame(result.findings).write_parquet(destination / "findings.parquet")
    evidence_frame(result.evidence).write_parquet(destination / "evidence.parquet")
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
