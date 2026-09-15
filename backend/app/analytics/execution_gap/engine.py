from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import polars as pl

from app.analytics.detectors.bundle import load_feature_bundle
from app.analytics.detectors.models import Evidence, Finding
from app.analytics.detectors.output import canonical_frame, order_evidence, order_findings
from app.analytics.execution_gap.definitions import DETECTORS, enabled_detectors
from app.analytics.execution_gap.evaluators import EVALUATORS
from app.analytics.execution_gap.manifest import write_manifest
from app.analytics.execution_gap.models import ExecutionGapRunResult

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "execution_gap"


def evaluate_all(feature_bundle: dict[str, pl.DataFrame]) -> ExecutionGapRunResult:
    findings: list[Finding] = []
    evidence: list[Evidence] = []
    evaluated: list[str] = []
    deferred: dict[str, str] = {}
    for detector in DETECTORS.values():
        if not detector.enabled:
            if detector.deferred_reason:
                deferred[detector.detector_id] = detector.deferred_reason
            continue
        evaluator = EVALUATORS[detector.detector_id]
        detector_findings, detector_evidence = evaluator(detector, feature_bundle)
        evaluated.append(detector.detector_id)
        findings.extend(detector_findings)
        evidence.extend(detector_evidence)
    ordered_findings = order_findings(findings)
    ordered_evidence = order_evidence(evidence, (item.id for item in ordered_findings))
    return ExecutionGapRunResult(findings=ordered_findings, evidence=ordered_evidence, detectors_evaluated=evaluated, deferred_detectors=deferred)


def write_outputs(result: ExecutionGapRunResult, output_dir: str | Path, dataset_id: str) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    canonical_frame(result.findings).write_parquet(destination / "findings.parquet")
    canonical_frame(result.evidence).write_parquet(destination / "evidence.parquet")
    write_manifest(destination, dataset_id, result)


def run_execution_gap(input_dir: str | Path, output_dir: str | Path = DEFAULT_OUTPUT, dataset_id: str | None = None) -> ExecutionGapRunResult:
    result = evaluate_all(load_feature_bundle(input_dir))
    write_outputs(result, output_dir, dataset_id or Path(input_dir).name)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAT-SA execution-gap detectors.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dataset-id")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_execution_gap(args.input, args.output, args.dataset_id)
    print(f"Detectors evaluated: {', '.join(result.detectors_evaluated)}")
    print(f"Findings: {len(result.findings)}")
    print(f"By detector: {dict(Counter(item.rule_id for item in result.findings))}")
    print(f"By severity: {dict(Counter(item.severity for item in result.findings))}")
    print(f"Baseline methods: {dict(Counter(DETECTORS[item].baseline_method for item in result.detectors_evaluated))}")
    print(f"Evidence: {len(result.evidence)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
