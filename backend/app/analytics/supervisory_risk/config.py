from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"

DIMENSIONS: list[str] = [
    "Escalation",
    "Investigation",
    "Remediation",
    "Monitoring",
    "Operational Discipline",
    "Cyber Resilience",
]

DIMENSION_WEIGHTS: dict[str, float] = {
    "Escalation": 0.25,
    "Investigation": 0.20,
    "Remediation": 0.20,
    "Monitoring": 0.15,
    "Operational Discipline": 0.10,
    "Cyber Resilience": 0.10,
}

RISK_BAND_THRESHOLDS: dict[str, tuple[float, float]] = {
    "LOW": (0.0, 24.999),
    "MODERATE": (25.0, 49.999),
    "HIGH": (50.0, 74.999),
    "CRITICAL": (75.0, 100.0),
}

PRIORITY_THRESHOLDS: dict[str, float] = {
    "HIGH": 70.0,
    "MEDIUM": 40.0,
    "LOW": 0.0,
}

# Explicit mapping of correlation groups to participating detectors, target operational dimension, and relevant feature names
CORRELATION_GROUPS: dict[str, dict[str, Any]] = {
    "CRITICAL_ESCALATION": {
        "dimension": "Escalation",
        "detectors": ["R002", "EG001", "PB001", "AN001"],
        "relevant_features": ["critical_escalation_rate", "escalation_rate"],
        "description": "Evaluation of critical alert and case escalation to management and response teams.",
    },
    "INVESTIGATION_EFFORT": {
        "dimension": "Investigation",
        "detectors": ["R004", "EG002", "PB002", "AN001"],
        "relevant_features": ["critical_median_investigation_minutes", "mean_investigation_minutes", "case_rate"],
        "description": "Evaluation of active investigation effort and duration dedicated to high/critical cases.",
    },
    "RAPID_CLOSURE": {
        "dimension": "Investigation",
        "detectors": ["R001", "EG004", "AN001"],
        "relevant_features": ["rapid_closure_rate", "critical_rapid_closure_rate"],
        "description": "Evaluation of premature or unusually rapid case closures.",
    },
    "UNINVESTIGATED_ALERTS": {
        "dimension": "Investigation",
        "detectors": ["NS005"],
        "relevant_features": [],
        "description": "Evaluation of critical alerts closed or discarded without an associated investigation case.",
    },
    "REMEDIATION": {
        "dimension": "Remediation",
        "detectors": ["R003", "EG003", "PB003", "AN001"],
        "relevant_features": ["remediation_rate"],
        "description": "Evaluation of whether identified security issues are remediated versus repeated indefinitely.",
    },
    "MONITORING_COVERAGE": {
        "dimension": "Monitoring",
        "detectors": ["R005", "NS001", "NS002", "PB004", "AN001"],
        "relevant_features": ["monitoring_coverage_rate", "alerts_per_asset", "cases_per_asset"],
        "description": "Evaluation of asset monitoring telemetry, inactive expected assets, and blindspots.",
    },
    "ACTIVITY_VOLATILITY": {
        "dimension": "Operational Discipline",
        "detectors": ["NS004"],
        "relevant_features": ["alert_count"],
        "description": "Evaluation of sudden drop-offs in observed entity activity against trailing history.",
    },
    "ANOMALY_PROFILE": {
        "dimension": "Cyber Resilience",
        "detectors": ["AN001"],
        "relevant_features": ["*"],  # Universal match for AN001's dedicated dimension
        "description": "Contextual multivariate anomaly detection indicating overall unusual operational profile.",
    },
}

# Corroboration parameters:
# Primary signal within a correlation group contributes its base normalized score.
# Corroborating signals from distinct upstream phases add a bounded boost, up to MAX_BOOST.
CORROBORATION_BOOST_PER_PHASE = 0.12
MAX_CORROBORATION_BOOST = 0.30

# Severity weights used when scaling record-level finding prevalence
SEVERITY_WEIGHTS: dict[str, float] = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.25,
}

# Evidence strength factor used for assessment strength derivation
EVIDENCE_STRENGTH_WEIGHTS: dict[str | None, float] = {
    "High": 1.0,
    "Medium": 0.75,
    "Low": 0.5,
    None: 0.65,  # Conservative explicit assessment fallback for unannotated Phase 5 findings
}

# AN001 is strictly contextual anomaly evidence and capped to prevent dominance over deterministic evidence
ANOMALY_SCORE_CEILING = 25.0

# Deferred detectors documented in earlier phases
DEFERRED_DETECTORS: dict[str, str] = {
    "EG005": "Deferred: lacks defensible documentation-quality standard baseline.",
    "NS003": "Deferred: no historical alert source expectation contract.",
    "NS006": "Deferred: avoid duplicating Phase 6 critical escalation execution gap.",
}
