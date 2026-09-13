# SAT-SA Context

## Purpose

SAT-SA (Supervisory Analytics Tool for SOC Assessment) is an offline platform for analysing periodic Security Operations Centre (SOC) alert, asset, case, and escalation submissions from Critical Sector Entities (CSEs).

The platform is intended to help supervisors identify operational evidence that may require review. It produces explainable operational signals and findings; it does not make final supervisory or compliance judgements.

## Domain Objects

- **Entity / CSE**: A supervised critical-sector organisation.
- **Asset**: A monitored or expected-to-be-monitored system belonging to an entity.
- **Alert**: A security detection associated with an entity and asset.
- **Case**: An investigation associated with an alert.
- **Escalation**: An escalation record associated with a case.
- **Feature**: A deterministic metric derived from canonical operational data.
- **Rule signal**: A deterministic condition evaluated against features.
- **Finding**: An explainable rule or detector result that describes an observed condition.
- **Evidence**: A traceable reference to an operational or derived feature record supporting a finding.

## Analytical Boundaries

The implemented analytical progression is:

1. **Phase 2**: Generate deterministic correlated synthetic SOC data.
2. **Phase 3**: Ingest CSV, JSON, and Parquet submissions into canonical Parquet.
3. **Phase 4**: Derive reusable operational features.
4. **Phase 5**: Evaluate isolated deterministic supervisory rules.
5. **Phase 6**: Detect potential execution gaps against configured expectations.
6. **Phase 7**: Detect unexpected absence of expected operational evidence.

Later phases are intentionally outside the current boundary:

- peer benchmarking
- statistical or machine-learning anomaly detection
- risk scoring
- review prioritisation
- dashboard workflows

## Interpretation Rules

- A feature is not automatically a finding.
- A finding is not an overall risk score.
- An execution gap means observed behaviour materially differs from an explicit expectation.
- Negative space means expected evidence had a sufficient opportunity to appear but was not observed.
- Evidence strength is not statistical confidence and does not imply statistical significance.
- Missing or insufficient data must not be silently converted into a negative conclusion.

## Data Semantics

Canonical datasets are stored as Parquet and are queryable with Polars and DuckDB. Datetimes use the project's canonical naive-UTC representation for cross-platform compatibility. Null durations mean the lifecycle event required to calculate the duration has not occurred or is unavailable.

Ground-truth controls used by synthetic-data generation remain outside analytical outputs and must not appear as feature, rule, or finding labels.
