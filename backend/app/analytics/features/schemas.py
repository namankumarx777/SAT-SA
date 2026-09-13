from __future__ import annotations

from typing import Any

RAPID_CLOSURE_MINUTES = 10
RECENT_ALERT_WINDOW_DAYS = 30
SCHEMA_VERSION = "1.0"

FEATURE_DEFINITIONS: list[dict[str, Any]] = [
    {"name": "acknowledgement_minutes", "type": "float", "source": ["alerts"], "formula": "acknowledged_at - timestamp", "nullable": True, "units": "minutes", "description": "Elapsed minutes to acknowledgement; null when unacknowledged."},
    {"name": "alert_lifetime_minutes", "type": "float", "source": ["alerts"], "formula": "closed_at - timestamp", "nullable": True, "units": "minutes", "description": "Elapsed minutes to closure; null for open alerts."},
    {"name": "has_case", "type": "bool", "source": ["alerts"], "formula": "case_id is not null", "nullable": False, "units": "boolean", "description": "Whether the alert has a related case."},
    {"name": "is_closed", "type": "bool", "source": ["alerts"], "formula": "status == Closed or closed_at is not null", "nullable": False, "units": "boolean", "description": "Whether the alert is closed."},
    {"name": "severity_rank", "type": "int", "source": ["alerts"], "formula": "Low=1, Medium=2, High=3, Critical=4", "nullable": False, "units": "ordinal", "description": "Ordinal severity representation."},
    {"name": "is_high_or_critical", "type": "bool", "source": ["alerts"], "formula": "severity in High, Critical", "nullable": False, "units": "boolean", "description": "Whether severity is high or critical."},
    {"name": "is_critical", "type": "bool", "source": ["alerts"], "formula": "severity == Critical", "nullable": False, "units": "boolean", "description": "Whether severity is critical."},
    {"name": "asset_alert_count", "type": "int", "source": ["alerts"], "formula": "count(alerts grouped by asset_id)", "nullable": False, "units": "alerts", "description": "Total alerts associated with the asset."},
    {"name": "asset_distinct_alert_sources", "type": "int", "source": ["alerts"], "formula": "n_unique(source) grouped by asset_id", "nullable": False, "units": "sources", "description": "Distinct alert sources observed for the asset."},
    {"name": "asset_recent_alert_count", "type": "int", "source": ["alerts"], "formula": "same-asset alerts in preceding 30 days, inclusive", "nullable": False, "units": "alerts", "description": "Recent same-asset alert activity; includes the current event."},
    {"name": "investigation_minutes", "type": "float", "source": ["cases"], "formula": "closed_at - opened_at", "nullable": True, "units": "minutes", "description": "Elapsed investigation minutes; null for open cases."},
    {"name": "case_age_at_close_minutes", "type": "float", "source": ["cases"], "formula": "closed_at - opened_at", "nullable": True, "units": "minutes", "description": "Case age at close; null for open cases."},
    {"name": "escalation_delay_minutes", "type": "float", "source": ["cases", "escalations"], "formula": "first escalation.created_at - case.opened_at", "nullable": True, "units": "minutes", "description": "Elapsed minutes to first escalation; null when not escalated."},
    {"name": "investigation_text_length", "type": "int", "source": ["cases"], "formula": "character length of investigation_text", "nullable": False, "units": "characters", "description": "Investigation text character count."},
    {"name": "investigation_word_count", "type": "int", "source": ["cases"], "formula": "whitespace-token count", "nullable": False, "units": "words", "description": "Approximate investigation text word count."},
    {"name": "monitoring_coverage_rate", "type": "float", "source": ["assets", "alerts"], "formula": "expected_monitored_assets_with_activity / expected_monitored_assets", "nullable": True, "units": "fraction in [0,1]", "description": "Observed coverage; null when expected_monitored_assets is zero."},
    {"name": "critical_asset_activity_rate", "type": "float", "source": ["assets", "alerts"], "formula": "critical_assets_with_activity / critical_assets", "nullable": True, "units": "fraction in [0,1]", "description": "Critical-asset activity coverage; null when critical_assets is zero."},
    {"name": "case_rate", "type": "float", "source": ["alerts", "cases"], "formula": "case_count / alert_count", "nullable": True, "units": "fraction in [0,1]", "description": "Cases per alert; null when alert_count is zero."},
    {"name": "escalation_rate", "type": "float", "source": ["cases"], "formula": "escalated_case_count / case_count", "nullable": True, "units": "fraction in [0,1]", "description": "Escalated cases divided by all cases; null when case_count is zero."},
    {"name": "critical_escalation_rate", "type": "float", "source": ["alerts", "cases"], "formula": "critical_escalated_case_count / critical_case_count", "nullable": True, "units": "fraction in [0,1]", "description": "Critical escalated cases divided by critical cases; null when critical_case_count is zero."},
    {"name": "remediation_rate", "type": "float", "source": ["cases"], "formula": "remediated closed cases / closed_case_count", "nullable": True, "units": "fraction in [0,1]", "description": "Remediated closed cases divided by closed cases; null when closed_case_count is zero."},
    {"name": "rapid_closure_rate", "type": "float", "source": ["cases"], "formula": "rapidly closed cases (<= 10 minutes) / closed_case_count", "nullable": True, "units": "fraction in [0,1]", "description": "Rapidly closed cases divided by closed cases."},
    {"name": "repeat_alert_event_rate", "type": "float", "source": ["alerts"], "formula": "repeat-alert events / alert_count", "nullable": True, "units": "fraction in [0,1]", "description": "Fraction of alert events occurring on assets with multiple alerts; null when alert_count is zero."},
    {"name": "repeat_alert_asset_rate", "type": "float", "source": ["assets", "alerts"], "formula": "assets with multiple alerts / active assets", "nullable": True, "units": "fraction in [0,1]", "description": "Fraction of active assets with multiple alerts; null when active assets is zero."},
    {"name": "asset_alert_rate_relative_to_entity", "type": "float", "source": ["assets", "alerts"], "formula": "asset alert_count / entity alert_count", "nullable": True, "units": "fraction in [0,1]", "description": "Asset share of entity alert events; null when entity alert_count is zero."},
    {"name": "alerts_per_asset", "type": "float", "source": ["assets", "alerts"], "formula": "alert_count / total_assets", "nullable": True, "units": "alerts per asset", "description": "Mean alert events per asset; null when total_assets is zero."},
    {"name": "cases_per_asset", "type": "float", "source": ["assets", "cases"], "formula": "case_count / total_assets", "nullable": True, "units": "cases per asset", "description": "Mean cases per asset; null when total_assets is zero."},
    {"name": "mean_investigation_minutes", "type": "float", "source": ["cases"], "formula": "mean(investigation_minutes)", "nullable": True, "units": "minutes", "description": "Mean closed-case duration; null when no closed investigations exist."},
    {"name": "median_investigation_minutes", "type": "float", "source": ["cases"], "formula": "median(investigation_minutes)", "nullable": True, "units": "minutes", "description": "Median closed-case duration; null when no closed investigations exist."},
    {"name": "critical_alert_rate", "type": "float", "source": ["alerts"], "formula": "critical_alert_count / alert_count", "nullable": True, "units": "fraction in [0,1]", "description": "Critical alerts divided by all alerts; null when alert_count is zero."},
    {"name": "high_critical_alert_rate", "type": "float", "source": ["alerts"], "formula": "(high_alert_count + critical_alert_count) / alert_count", "nullable": True, "units": "fraction in [0,1]", "description": "High or critical alerts divided by all alerts; null when alert_count is zero."},
    {"name": "critical_rapid_closure_rate", "type": "float", "source": ["cases", "alerts"], "formula": "critical rapidly closed cases / critical_closed_case_count", "nullable": True, "units": "fraction in [0,1]", "description": "Critical cases closed within the threshold divided by closed critical cases; null when none are closed."},
]


def feature_definitions(tables: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return machine-readable definitions, including preserved canonical columns."""
    definitions = {definition["name"]: definition.copy() for definition in FEATURE_DEFINITIONS}
    if tables:
        for table_name, frame in tables.items():
            for column in frame.columns:
                definitions.setdefault(column, {
                    "name": column,
                    "type": str(frame.schema[column]),
                    "source": [table_name.replace("_features", "")],
                    "formula": f"preserved canonical column {column}",
                    "nullable": frame[column].null_count() > 0,
                    "units": "native",
                    "description": f"Canonical operational field preserved in {table_name}.",
                })
    return list(definitions.values())
