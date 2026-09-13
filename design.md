# SAT-SA Design

## Architecture

SAT-SA follows a local, file-based analytical pipeline:

```text
CSE submission
    -> Phase 3 ingestion and validation
    -> canonical Parquet
    -> Phase 4 feature engineering
    -> feature Parquet
    -> Phase 5 deterministic rules
    -> Phase 6 execution-gap detectors
    -> Phase 7 negative-space detectors
    -> findings and evidence Parquet
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

## Storage Contracts

Phase outputs are kept separate:

- Phase 5: `data/processed/<run>/findings.parquet`
- Phase 6: `data/processed/execution_gap/findings.parquet`
- Phase 7: `data/processed/negative_space/findings.parquet`

Each detector stage also writes an evidence Parquet file and a stage-specific manifest. Outputs are directly queryable with DuckDB.

## API Boundaries

The backend exposes thin route handlers for:

- ingestion validation/import
- Phase 5 rule execution and findings
- Phase 6 execution-gap execution and findings
- Phase 7 negative-space execution and findings

Business logic remains in the analytics packages rather than in FastAPI handlers.

## Non-Goals

This design intentionally does not include:

- peer benchmarking
- machine-learning or statistical anomaly detection
- final risk scoring
- review prioritisation
- authentication
- PostgreSQL
- cloud storage
- external services
- dashboard presentation
