from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import polars as pl

from app.analytics.detectors.bundle import load_feature_bundle
from app.analytics.detectors.output import canonical_frame, order_evidence, order_findings
from app.analytics.negative_space.baselines import observation_window
from app.analytics.negative_space.definitions import DETECTORS, enabled_detectors
from app.analytics.negative_space.evaluators import EVALUATORS
from app.analytics.negative_space.models import NegativeSpaceRunResult

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "negative_space"


def evaluate_all(bundle: dict[str, pl.DataFrame]) -> NegativeSpaceRunResult:
    window = observation_window(bundle)
    findings, evidence, evaluated, deferred = [], [], [], {}
    for detector in DETECTORS.values():
        if not detector.enabled:
            if detector.deferred_reason:
                deferred[detector.detector_id] = detector.deferred_reason
            continue
        evaluator = EVALUATORS[detector.detector_id]
        detector_findings, detector_evidence = evaluator(detector, bundle, window)
        evaluated.append(detector.detector_id)
        findings.extend(detector_findings)
        evidence.extend(detector_evidence)
    ordered_findings = order_findings(findings)
    ordered_evidence = order_evidence(evidence, (item.id for item in ordered_findings))
    return NegativeSpaceRunResult(findings=ordered_findings, evidence=ordered_evidence, detectors_evaluated=evaluated, deferred_detectors=deferred, observation_window=window)


def write_outputs(result: NegativeSpaceRunResult, output_dir: str | Path, dataset_id: str) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    canonical_frame(result.findings).write_parquet(destination / "findings.parquet")
    canonical_frame(result.evidence).write_parquet(destination / "evidence.parquet")
    manifest = {
        "schema_version": "1.0", "dataset_id": dataset_id,
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "detectors": list(DETECTORS), "enabled_detectors": result.detectors_evaluated,
        "deferred_detectors": result.deferred_detectors,
        "expectation_methods": {key: value.expectation_method for key, value in DETECTORS.items()},
        "thresholds": {key: value.thresholds for key, value in DETECTORS.items()},
        "observation_window": result.observation_window.model_dump(),
        "evidence_strength_method": "Evidence strength reflects population size, absence magnitude, expectation strength, and observation sufficiency; it is not statistical confidence.",
        "row_counts": {"findings": len(result.findings), "evidence": len(result.evidence)},
    }
    (destination / "negative_space_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_negative_space(input_dir: str | Path, output_dir: str | Path = DEFAULT_OUTPUT, dataset_id: str | None = None) -> NegativeSpaceRunResult:
    result = evaluate_all(load_feature_bundle(input_dir))
    write_outputs(result, output_dir, dataset_id or Path(input_dir).name)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAT-SA negative-space detectors.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dataset-id")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_negative_space(args.input, args.output, args.dataset_id)
    print(f"Observation window: {result.observation_window.start} to {result.observation_window.end}")
    print(f"Detectors evaluated: {', '.join(result.detectors_evaluated)}")
    print(f"Deferred detectors: {result.deferred_detectors}")
    print(f"Findings: {len(result.findings)}")
    print(f"By detector: {dict(Counter(item.rule_id for item in result.findings))}")
    print(f"By severity: {dict(Counter(item.severity for item in result.findings))}")
    print(f"Evidence: {len(result.evidence)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
