from __future__ import annotations

from collections.abc import Callable

import polars as pl

from app.analytics.execution_gap.baselines import confidence_for_gap, population_median
from app.analytics.execution_gap.definitions import (
    CRITICAL_ESCALATION_EXPECTED_RATE,
    CRITICAL_INVESTIGATION_MINUTES,
    INVESTIGATION_RATIO_THRESHOLD,
    MAX_RAPID_CLOSURE_BASELINE,
    MIN_CRITICAL_CASES,
    MIN_CLOSED_CASES,
    MIN_ESCALATION_GAP,
    MIN_RAPID_CLOSURE_GAP,
    MIN_REMEDIATION_GAP,
    REMEDIATION_MIN_RATE,
)
from app.analytics.execution_gap.evidence import case_evidence, execution_finding, feature_evidence
from app.analytics.execution_gap.models import ExecutionGapDefinition
from app.analytics.rules.models import Evidence, Finding

Bundle = dict[str, pl.DataFrame]
Evaluator = Callable[[ExecutionGapDefinition, Bundle], tuple[list[Finding], list[Evidence]]]


def _relative_gap(expected: float, observed: float) -> float | None:
    return None if expected == 0 else (expected - observed) / abs(expected)


def evaluate_eg001(detector: ExecutionGapDefinition, bundle: Bundle) -> tuple[list[Finding], list[Evidence]]:
    rows = bundle["entity_features"].filter(
        (pl.col("critical_case_count") >= MIN_CRITICAL_CASES)
        & pl.col("critical_escalation_rate").is_not_null()
        & (pl.col("critical_escalation_rate") <= CRITICAL_ESCALATION_EXPECTED_RATE - MIN_ESCALATION_GAP)
    ).sort("entity_id").to_dicts()
    findings, evidence = [], []
    for row in rows:
        observed = float(row["critical_escalation_rate"]); expected = CRITICAL_ESCALATION_EXPECTED_RATE; gap = expected - observed
        confidence = confidence_for_gap(int(row["critical_case_count"]), gap)
        finding = execution_finding(detector_id="EG001", entity_id=row["entity_id"], finding_type="Execution Gap", severity="High", confidence=confidence, title="Potential critical escalation execution gap", summary=f"{row['entity_id']}'s critical-case escalation rate is materially below the configured baseline.", rationale=f"Expected critical escalation rate: {expected:.1%}. Observed rate: {observed:.1%}. Gap: {gap:.1%}. Population: {row['critical_case_count']} critical cases. This indicates a potential execution weakness, not a confirmed control failure.", metric_name="critical_escalation_rate", observed=observed, expected=expected, population_size=int(row["critical_case_count"]), absolute_gap=gap, relative_gap=_relative_gap(expected, observed), baseline_method="configured_supervisory_expectation")
        findings.append(finding); evidence.extend(feature_evidence(finding, row["entity_id"], ["critical_case_count", "critical_escalated_case_count", "critical_escalation_rate"], row))
        if "case_features" in bundle:
            cases = bundle["case_features"].filter((pl.col("entity_id") == row["entity_id"]) & (pl.col("severity") == "Critical")).sort("id").head(10).to_dicts()
            evidence.extend(case_evidence(finding, cases, ["id", "severity", "is_escalated"]))
    return findings, evidence


def evaluate_eg002(detector: ExecutionGapDefinition, bundle: Bundle) -> tuple[list[Finding], list[Evidence]]:
    reference = population_median(bundle["entity_features"], "critical_median_investigation_minutes", "critical_case_count", MIN_CRITICAL_CASES)
    expected = float(CRITICAL_INVESTIGATION_MINUTES)
    rows = bundle["entity_features"].filter((pl.col("critical_case_count") >= MIN_CRITICAL_CASES) & pl.col("critical_median_investigation_minutes").is_not_null() & (pl.col("critical_median_investigation_minutes") < expected * INVESTIGATION_RATIO_THRESHOLD)).sort("entity_id").to_dicts()
    findings, evidence = [], []
    for row in rows:
        observed = float(row["critical_median_investigation_minutes"]); gap = expected - observed; ratio = observed / expected
        finding = execution_finding(detector_id="EG002", entity_id=row["entity_id"], finding_type="Execution Gap", severity="High", confidence=confidence_for_gap(int(row["critical_case_count"]), gap / expected), title="Potentially insufficient investigation effort relative to configured expectation", summary=f"{row['entity_id']}'s critical-case investigation duration is materially below the configured minimum expectation.", rationale=f"Configured minimum expectation: {expected:.1f} minutes. Observed median: {observed:.1f} minutes. Observed/expectation ratio: {ratio:.2f}. Population: {row['critical_case_count']} critical cases. Reference population median: {reference.value:.1f} minutes when available. This is a potential execution gap, not a definitive investigation assessment.", metric_name="critical_median_investigation_minutes", observed=observed, expected=expected, population_size=int(row["critical_case_count"]), absolute_gap=gap, relative_gap=gap / expected, baseline_method="configured_minimum", reference_value=reference.value)
        findings.append(finding); evidence.extend(feature_evidence(finding, row["entity_id"], ["critical_case_count", "critical_median_investigation_minutes"], row))
    return findings, evidence


def evaluate_eg003(detector: ExecutionGapDefinition, bundle: Bundle) -> tuple[list[Finding], list[Evidence]]:
    reference = population_median(bundle["entity_features"], "remediation_rate", "closed_case_count", MIN_CLOSED_CASES)
    expected = float(REMEDIATION_MIN_RATE)
    rows = bundle["entity_features"].filter((pl.col("closed_case_count") >= MIN_CLOSED_CASES) & pl.col("remediation_rate").is_not_null() & (pl.col("remediation_rate") <= expected - MIN_REMEDIATION_GAP)).sort("entity_id").to_dicts()
    findings, evidence = [], []
    for row in rows:
        observed = float(row["remediation_rate"]); gap = expected - observed
        finding = execution_finding(detector_id="EG003", entity_id=row["entity_id"], finding_type="Execution Gap", severity="High", confidence=confidence_for_gap(int(row["closed_case_count"]), gap), title="Potential remediation execution gap", summary=f"{row['entity_id']}'s remediation rate is materially below the configured minimum expectation.", rationale=f"Configured minimum expectation: {expected:.1%}. Observed rate: {observed:.1%}. Gap: {gap:.1%}. Population: {row['closed_case_count']} closed cases. Reference population median: {reference.value:.1%} when available. This is a potential remediation execution gap, not a confirmed failure.", metric_name="remediation_rate", observed=observed, expected=expected, population_size=int(row["closed_case_count"]), absolute_gap=gap, relative_gap=_relative_gap(expected, observed), baseline_method="configured_minimum", reference_value=reference.value)
        findings.append(finding); evidence.extend(feature_evidence(finding, row["entity_id"], ["closed_case_count", "remediated_case_count", "remediation_rate"], row))
    return findings, evidence


def evaluate_eg004(detector: ExecutionGapDefinition, bundle: Bundle) -> tuple[list[Finding], list[Evidence]]:
    rows = bundle["entity_features"].filter((pl.col("closed_case_count") >= MIN_CLOSED_CASES) & pl.col("rapid_closure_rate").is_not_null() & (pl.col("rapid_closure_rate") >= MAX_RAPID_CLOSURE_BASELINE + MIN_RAPID_CLOSURE_GAP)).sort("entity_id").to_dicts()
    findings, evidence = [], []
    for row in rows:
        observed = float(row["rapid_closure_rate"]); expected = MAX_RAPID_CLOSURE_BASELINE; gap = observed - expected
        finding = execution_finding(detector_id="EG004", entity_id=row["entity_id"], finding_type="Execution Gap", severity="Medium", confidence=confidence_for_gap(int(row["closed_case_count"]), gap), title="Potential rapid-closure execution gap", summary=f"{row['entity_id']}'s rapid-closure rate is materially above the configured expected maximum.", rationale=f"Expected maximum rapid-closure rate: {expected:.1%}. Observed rate: {observed:.1%}. Gap: {gap:.1%}. Population: {row['closed_case_count']} closed cases. This is a systematic operational signal, not a confirmed control failure.", metric_name="rapid_closure_rate", observed=observed, expected=expected, population_size=int(row["closed_case_count"]), absolute_gap=gap, relative_gap=gap / expected, baseline_method="configured_supervisory_expectation")
        findings.append(finding); evidence.extend(feature_evidence(finding, row["entity_id"], ["closed_case_count", "rapid_closure_count", "rapid_closure_rate"], row))
    return findings, evidence


EVALUATORS: dict[str, Evaluator] = {"EG001": evaluate_eg001, "EG002": evaluate_eg002, "EG003": evaluate_eg003, "EG004": evaluate_eg004}
