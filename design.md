# SENTRA Design

## Architecture

SENTRA follows a local, file-based analytical pipeline:

```text
CSE submission
    -> Phase 3 ingestion and validation
    -> canonical Parquet
    -> Phase 4 feature engineering
    -> feature Parquet
    -> Phase 5 deterministic rules
    -> Phase 6 execution-gap detectors
    -> Phase 7 negative-space detectors
    -> Phase 8 peer benchmarking & anomaly detection
    -> Phase 9 supervisory risk & review prioritisation
    -> entity_risk, risk_contributions, review_queue Parquet
```

All stages run offline with Python, Polars, Pydantic, PyArrow, DuckDB, and the standard library.

## Canonical Data Layer

Phase 3 normalizes these tables:

- `entities`
- `assets`
- `alerts`
- `cases`
- `escalations`

A successful ingestion creates a unique processed dataset directory and a manifest containing source filenames, sizes, SHA-256 hashes, row counts, and validation status.

## Feature Layer

Phase 4 reads canonical Parquet and writes:

- `alert_features.parquet`
- `case_features.parquet`
- `asset_features.parquet`
- `entity_features.parquet`
- `entity_month_features.parquet`
- `feature_manifest.json`

Features are deterministic, null-safe, and operationally descriptive. Examples include lifecycle durations, severity indicators, monitoring coverage, repeated-alert activity, remediation rates, and monthly activity.

Monthly features contain only observed entity-months. Missing months are not automatically imputed as zero.

## Finding and Evidence Architecture

Phase 5, Phase 6, and Phase 7 reuse the shared `Finding` and `Evidence` models.

```text
Finding
  rule_id / detector_id
  entity_id
  finding_type
  severity
  evidence_strength
  rationale
  baseline metadata
       |
       +-- Evidence
             source_type
             source_id
             entity_id
             field
             value
             reason
```

Finding IDs and evidence IDs are deterministic SHA-256-derived identifiers. Outputs are sorted deterministically before Parquet serialization.

## Phase 5: Rule Signals

Phase 5 evaluates isolated operational conditions:

- R001: critical alert closed rapidly
- R002: critical alert without escalation
- R003: repeated alerts without remediation
- R004: short high/critical investigation
- R005: low monitoring coverage

These are record-level or direct operational signals. They do not calculate entity risk.

## Phase 6: Execution Gaps

Phase 6 compares entity behaviour with configured supervisory expectations:

- EG001: critical escalation minimum of 60%
- EG002: critical investigation minimum of 20 minutes
- EG003: remediation minimum of 75%
- EG004: rapid-closure maximum of 10%

Population medians may be retained as reference context but are not execution requirements. EG005 is deferred because the current feature contract lacks a defensible documentation-quality expectation.

Execution findings include baseline type, baseline method, baseline value, observed value, gap value, gap direction, population size, and evidence strength.

## Phase 7: Negative Space

Phase 7 detects absence of expected evidence rather than generic low values:

- NS001: expected-monitored assets without activity
- NS002: critical assets without security activity
- NS003: deferred due to missing source expectations
- NS004: low activity against the entity's own trailing history
- NS005: critical alerts without associated cases
- NS006: deferred to avoid duplicating Phase 6 escalation-gap analysis

The engine derives an observation window from usable alert and case timestamps. Time-dependent findings are suppressed when the observation window is insufficient.

Negative-space findings use explicit expectation methods such as `EXPECTED_MONITORING`, `CONFIGURED_EXPECTATION`, and `DERIVED_EXPECTATION`. Peer cohorts are not used.

## Phase 8: Peer Benchmarking and Anomaly Detection

Phase 8 compares entities against structural cohorts `(sector, size, criticality)` and identifies global multivariate outliers:

- PB001: Critical escalation peer deviation
- PB002: Investigation duration peer deviation
- PB003: Remediation rate peer deviation
- PB004: Operational volume per asset deviation
- AN001: Unusual operational profile (PyOD Isolation Forest on 10 operational features)

AN001 anomaly scores are treated strictly as contextual anomaly signals, not probabilities or regulatory non-compliance judgements.

## Phase 9: Supervisory Risk Engine and Manual Review Prioritisation

Phase 9 aggregates heterogeneous outputs from Phases 5–8 into:

1. **Entity-Level Supervisory Risk Indicator**:
   - Level 1: Derived across 6 operational dimensions (`Escalation`, `Investigation`, `Remediation`, `Monitoring`, `Operational Discipline`, `Cyber Resilience`).
   - Level 2: Assessable-weighted overall score (0–100) and risk band (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
   - Anti-double-counting correlation groups (`CRITICAL_ESCALATION`, `INVESTIGATION_EFFORT`, `RAPID_CLOSURE`, `REMEDIATION`, `MONITORING_COVERAGE`, etc.) ensure overlapping detectors reinforce corroboration rather than multiplying risk.
   - Record-level findings from Phase 5 are normalized using entity denominators into signal prevalence rates.
2. **Supervisory Manual-Review Priority Queue**:
   - Distinct from risk score: Prioritises systemic execution gaps (Phase 6), unmonitored blindspots (Phase 7), multi-phase corroboration, and evidence strength.
   - Rank-ordered queue output with `HIGH`, `MEDIUM`, `LOW` review urgency.
3. **Traceable Risk Contributions & Auditable Manifest**:
   - `risk_contributions.parquet` linking every score back to underlying finding IDs.
   - `supervisory_risk_manifest.json` recording weights, thresholds, methods, and excluded detectors.

## Phase 10: SENTRA Supervisory Dashboard & SIH Demo Workflow

Phase 10 provides the supervisor-facing offline dashboard turning backend analytical models into an intuitive supervisory assessment workflow:

1. **National Overview (`/`)**: Executive KPIs, national risk distribution, and ranked entity table with quick filtering.
2. **CSE Assessments (`/cses`)**: Comprehensive sortable/searchable registry across all 6 operational dimensions.
3. **CSE Detail View (`/cses/[entityId]`)**:
   - Master entity card and risk score gauge.
   - 6 Operational Dimension Cards with dynamic assessability handling (`Not Assessable` for missing baselines).
   - Horizontal dimension comparison bar chart and radar polygon.
   - **Why Flagged Deep-Dive**: Explaining elevated dimensions through multi-phase corroboration and quantitative gaps.
   - **Traceable Risk Contributions**: Interactive drawer viewing finding metadata and underlying source evidence records (`case_feature`, `asset`, `recorded_value`, reason).
4. **Supervisory Review Queue (`/review-queue`)**: Triage workflow clearly communicating `Review Priority ≠ Risk Score`, elevating systemic execution gaps and blindspots.
5. **Supervisory Analytics (`/analytics`)**: Sector risk profiles, dimension frequency, and population band distribution.
6. **Data Quality & Limitations (`/data-quality`)**: Assessment completeness transparency, unassessable dimension rules, and manifest metadata viewer.

## Storage Contracts

Phase outputs are kept separate:

- Phase 5: `data/processed/phase5-final/findings.parquet`
- Phase 6: `data/processed/execution_gap-final/findings.parquet`
- Phase 7: `data/processed/negative_space-final/findings.parquet`
- Phase 8: `data/processed/peer_anomaly-final/findings.parquet`
- Phase 9: `data/processed/supervisory_risk-final/` (`entity_risk.parquet`, `risk_contributions.parquet`, `review_queue.parquet`, `supervisory_risk_manifest.json`)

All Parquet outputs are deterministically sorted and directly queryable with DuckDB and Polars.

## API Boundaries

The backend exposes thin route handlers for:

- Ingestion validation/import (`/ingestion`)
- Phase 5 rule execution and findings (`/analytics/rules`, `/findings`)
- Phase 6 execution-gap execution and findings (`/analytics/execution-gap`)
- Phase 7 negative-space execution and findings (`/analytics/negative-space`)
- Phase 8 peer benchmarking and anomaly detection (`/analytics/peer-anomaly`)
- Phase 9 supervisory risk assessment, review queue, manifest, and finding detail (`/analytics/supervisory-risk`)

Business logic remains in the analytics packages rather than in FastAPI handlers.

## Non-Goals

This design intentionally does not include:

- autonomous regulatory enforcement decisions
- SOC analyst replacement or automated alert triage
- probabilistic risk modeling (scores are operational supervisory indicators, not probabilities)
- live event streaming or SIEM consoles
- authentication SaaS or external cloud dependencies
- PostgreSQL or external database engines
- cloud storage or external API dependencies
