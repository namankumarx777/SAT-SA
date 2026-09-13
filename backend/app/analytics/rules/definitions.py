from __future__ import annotations

from app.analytics.features.schemas import RAPID_CLOSURE_MINUTES
from app.analytics.rules.models import RuleDefinition

MIN_REPEATED_ALERTS = 3
MIN_MONITORING_GAP_ASSETS = 5
MIN_MONITORING_COVERAGE = 0.90
MIN_CRITICAL_CASES = 5
MIN_EXPECTED_MONITORED_ASSETS = 10

RULES: dict[str, RuleDefinition] = {
    "R001": RuleDefinition(
        rule_id="R001", name="Critical Alert Closed Rapidly",
        description="Identify critical cases closed at or below the rapid-closure threshold.",
        finding_type="Rapid Closure", severity="Medium",
        thresholds={"rapid_closure_minutes": RAPID_CLOSURE_MINUTES},
    ),
    "R002": RuleDefinition(
        rule_id="R002", name="Critical Alert Without Escalation",
        description="Identify critical cases with no associated escalation.",
        finding_type="Escalation", severity="High",
        thresholds={"minimum_critical_cases": MIN_CRITICAL_CASES},
    ),
    "R003": RuleDefinition(
        rule_id="R003", name="Repeated Alerts Without Remediation",
        description="Identify assets with repeated alerts whose associated cases have no recorded remediation.",
        finding_type="Repeated Activity", severity="Medium",
        thresholds={"minimum_repeated_alerts": MIN_REPEATED_ALERTS},
    ),
    "R004": RuleDefinition(
        rule_id="R004", name="Investigation Duration Anomaly Proxy",
        description="Identify high or critical cases with short investigation duration.",
        finding_type="Investigation", severity="Medium",
        thresholds={"investigation_minutes": RAPID_CLOSURE_MINUTES},
    ),
    "R005": RuleDefinition(
        rule_id="R005", name="Very Low Monitoring Activity on Expected-Monitored Assets",
        description="Identify entities with low observed activity among sufficiently numerous expected-monitored assets.",
        finding_type="Monitoring Coverage", severity="Medium",
        thresholds={
            "minimum_gap_assets": MIN_MONITORING_GAP_ASSETS,
            "maximum_coverage": MIN_MONITORING_COVERAGE,
            "minimum_expected_assets": MIN_EXPECTED_MONITORED_ASSETS,
        },
    ),
}


def enabled_rules() -> list[RuleDefinition]:
    """Return enabled definitions in stable rule order."""
    return [rule for rule in RULES.values() if rule.enabled]
