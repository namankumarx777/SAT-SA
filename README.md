# SAT-SA — Supervisory Analytics Tool for SOC Assessment

**SAT-SA** is an offline supervisory analytics tool developed for the **Smart India Hackathon (SIH)**. It evaluates periodic Security Operations Centre (SOC) submissions (alerts, cases, assets, escalations) from Critical Sector Entities (CSEs) to help regulators and supervisors identify operational weaknesses, systemic execution gaps, and unmonitored blindspots.

---

## What SAT-SA Does

- **Multi-Dimensional Supervisory Risk Assessment**: Evaluates entities across 6 operational dimensions (*Escalation*, *Investigation*, *Remediation*, *Monitoring*, *Operational Discipline*, *Cyber Resilience*).
- **Anti-Double-Counting Correlation**: Consolidates overlapping deterministic rules, execution gaps, peer cohort benchmarks, and anomaly detectors into unified correlation groups with bounded corroboration boosts.
- **Manual Review Prioritization**: Generates a ranked triage queue optimizing human inspector time by prioritizing systemic execution gaps and blindspots over raw record volume (`Review Priority ≠ Risk Score`).
- **100% Traceable Evidence Chain**: Every risk score, dimension rating, and review queue recommendation links directly to standardized finding IDs and granular source records (`case_feature`, `asset`, `recorded_value`).
- **Conservative Missing-Data Handling**: Missing telemetry or absent denominators are marked `Not Assessable` and dynamically excluded from the weighted average denominator (*Unassessable ≠ Low Risk*).
- **100% Offline Capable**: Built with FastAPI, Next.js, Polars, and DuckDB; requires zero external network, cloud, or database services.

---

## What SAT-SA Does NOT Do

- Not a SIEM or live SOC event monitor.
- Not an automated incident response tool or packet analyzer.
- Not an autonomous regulatory enforcement decision-maker.
- Not a probabilistic risk predictor (scores are bounded operational risk indicators, not probabilities).
- Does not use LLMs, cloud AI APIs, or authentication SaaS.

---

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Polars, PyOD (Isolation Forest), DuckDB, Pydantic v2, Pytest.
- **Frontend**: Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS, Recharts, Lucide Icons.
- **Data Storage**: Apache Parquet canonical tables (fast, deterministic, zero external database).

---

## Getting Started

### 1. Prerequisites
- Python 3.11 or later
- Node.js 18 or later
- npm

### 2. Backend Setup
```powershell
# Navigate to backend directory and activate venv
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run backend API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend
npm install

# Run frontend development server
npm run dev
```

The dashboard is accessible at: `http://localhost:3000`

---

## Running Analytics & Tests

### Run Backend Test Suite (90+ Tests)
```powershell
backend\.venv\Scripts\pytest.exe -q tests
```

### Build Frontend for Production
```powershell
cd frontend
npm run build
```

### Regenerate Phase 9 Supervisory Risk Parquet Artifacts
```powershell
$env:PYTHONPATH="backend"
python -m app.analytics.supervisory_risk.engine --input data/processed --output data/processed/supervisory_risk-final
```

---

## SIH Demonstration Workflow

For the complete 90–120 second demonstration script, see:
[`docs/SIH_DEMO_SCRIPT.md`](docs/SIH_DEMO_SCRIPT.md)

1. **National Overview (`/`)**: Portfolio-level KPI snapshot across 12 CSEs.
2. **CSE Risk Ranking (`/cses`)**: Identify Rank #1 outlier: **`CSE-011`** (North Grid 11 Energy, HIGH Risk Band, 53.22/100).
3. **CSE Detail View (`/cses/CSE-011`)**: Inspect 6 dimension cards, radar polygon, and dimensional decomposition (*Investigation: 100/100, Escalation: 93/100*).
4. **Why Flagged?**: Multi-phase corroboration showing how independent detectors (`R004`, `EG002`, `PB002`, `AN001`) are consolidated without quadruple-counting.
5. **Finding & Evidence Inspector**: Open drawer to see quantitative gaps and granular source record evidence.
6. **Supervisory Review Queue (`/review-queue`)**: Inspect Rank #1 recommendation (*EG002: Insufficient investigation duration gap, Priority Score 100.0*).

---

## Documentation

- [Architecture Specification](docs/ARCHITECTURE.md)
- [SIH Demonstration Script](docs/SIH_DEMO_SCRIPT.md)
- [Context & Analytical Principles](context.md)
- [Detailed System Design](design.md)
