from __future__ import annotations

from app.analytics.execution_gap.models import ExecutionGapDefinition

MIN_CRITICAL_CASES = 5
MIN_CLOSED_CASES = 10
MIN_ESCALATION_GAP = 0.15
MIN_REMEDIATION_GAP = 0.15
MAX_RAPID_CLOSURE_BASELINE = 0.10
MIN_RAPID_CLOSURE_GAP = 0.15
INVESTIGATION_RATIO_THRESHOLD = 0.60
CRITICAL_INVESTIGATION_MINUTES = 20
REMEDIATION_MIN_RATE = 0.75
CRITICAL_ESCALATION_EXPECTED_RATE = 0.60
MAX_EVIDENCE_CASES = 10

DETECTORS: dict[str, ExecutionGapDefinition] = {
    "EG001": ExecutionGapDefinition(
        detector_id="EG001", name="Critical Escalation Execution Gap",
        description="Critical-case escalation is materially below the configured supervisory expectation.",
        severity="High", thresholds={"minimum_critical_cases": MIN_CRITICAL_CASES, "minimum_gap": MIN_ESCALATION_GAP, "expected_rate": CRITICAL_ESCALATION_EXPECTED_RATE},
        baseline_method="configured_supervisory_expectation", direction="lower_is_gap",
    ),
    "EG002": ExecutionGapDefinition(
        detector_id="EG002", name="Investigation Effort Execution Gap",
        description="Critical-case investigation duration is materially below the configured minimum expectation.",
        severity="High", thresholds={"minimum_critical_cases": MIN_CRITICAL_CASES, "minimum_ratio": INVESTIGATION_RATIO_THRESHOLD, "minimum_expected_minutes": CRITICAL_INVESTIGATION_MINUTES},
        baseline_method="configured_minimum", direction="lower_is_gap",
    ),
    "EG003": ExecutionGapDefinition(
        detector_id="EG003", name="Remediation Execution Gap",
        description="Closed-case remediation rate is materially below the configured minimum expectation.",
        severity="High", thresholds={"minimum_closed_cases": MIN_CLOSED_CASES, "minimum_gap": MIN_REMEDIATION_GAP, "minimum_expected_rate": REMEDIATION_MIN_RATE},
        baseline_method="configured_minimum", direction="lower_is_gap",
    ),
    "EG004": ExecutionGapDefinition(
        detector_id="EG004", name="Rapid Closure Execution Gap",
        description="Entity rapid-closure rate is materially above the configured expected maximum.",
        severity="Medium", thresholds={"minimum_closed_cases": MIN_CLOSED_CASES, "minimum_gap": MIN_RAPID_CLOSURE_GAP, "maximum_expected_rate": MAX_RAPID_CLOSURE_BASELINE},
        baseline_method="configured_supervisory_expectation", direction="higher_is_gap",
    ),
    "EG005": ExecutionGapDefinition(
        detector_id="EG005", name="Investigation Documentation Execution Gap",
        description="Deferred: current feature contract does not provide sufficient evidence for a defensible documentation-quality detector.",
        severity="Medium", enabled=False, thresholds={}, baseline_method="deferred", direction="lower_is_gap",
        deferred_reason="Current features provide text length and word count but no documented expected documentation standard or quality baseline.",
    ),
}


def enabled_detectors() -> list[ExecutionGapDefinition]:
    return [detector for detector in DETECTORS.values() if detector.enabled]
