# SENTRA — Smart India Hackathon (SIH) Demonstration Script

**Title**: SENTRA: Supervisory Analytics Tool for SOC Assessment  
**Target Duration**: 90–120 Seconds  
**Demonstration Mode**: Offline / Local Assessment Environment  
**Primary Demonstration Entity**: `CSE-011` (North Grid 11 Energy)  

---

## 0:00 – 0:15 | The National Portfolio Snapshot

1. **Open SENTRA Dashboard (`http://localhost:3000`)**:
   - Point to the Top Header: *Offline Assessment • Local Engine*.
   - Point to the 5 executive KPI cards:
     - **12 Assessed CSEs** across Critical Infrastructure sectors.
     - **0 Critical Risk** entities.
     - **1 High Risk CSE (`CSE-011`)**.
     - **21 Items Requiring Review** (`9 High Urgency`).
     - **100% Assessment Coverage** across telemetry.
2. **Explain the National Risk Distribution**:
   - *"SENTRA ingests periodic SOC submissions from critical sector entities and evaluates them across 6 operational dimensions without requiring live event streaming or cloud dependencies."*

---

## 0:15 – 0:35 | Identifying the Outlier: CSE-011

1. **Locate `CSE-011` (North Grid 11 Energy)** in the National Risk Ranking table:
   - Rank **#1** with an Overall Supervisory Risk Score of **`53.22 / 100`** (`HIGH` Risk Band).
   - Top Risk Driver: **`Investigation`**.
2. **Click `Inspect Primary Demo: CSE-011`**:
   - Navigate to `/cses/CSE-011`.

---

## 0:35 – 0:55 | Decomposing Dimensional Risk for CSE-011

1. **Present the 6 Operational Dimension Cards & Radar Polygon**:
   - **Investigation:** `100.00 / 100` (Critical Concern)
   - **Escalation:** `93.00 / 100` (Critical Concern)
   - **Remediation:** `40.59 / 100` (Moderate Gap)
   - **Monitoring:** `0.00 / 100` (Normal baseline — feature-aware isolation prevents phantom anomaly leakage)
   - **Operational Discipline:** `0.00 / 100`
   - **Cyber Resilience:** `18.55 / 100` (Contextual multivariate outlier score)
2. **Explain**:
   - *"The entity's high risk is concentrated in investigation duration failures and unescalated critical cases, rather than a broad across-the-board collapse."*

---

## 0:55 – 1:15 | Anti-Double-Counting & Corroboration ("Why Flagged?")

1. **Scroll down to "Why was this Entity Flagged?"**:
   - Highlight the **Investigation Risk (100.0/100)** breakdown:
     - Corroborated by **`R004`** (Rule: low investigation duration), **`EG002`** (Execution Gap: 12.5 min median gap vs 20.0 min baseline), **`PB002`** (Peer Deviation), and **`AN001`** (Contextual Anomaly).
2. **Key Differentiator**:
   - *"When four independent detectors identify the same operational weakness, SENTRA consolidates them into ONE correlation group (`INVESTIGATION_EFFORT`) with a bounded corroboration boost (+24%), rather than naively summing the penalties to an absurd >200 score."*

---

## 1:15 – 1:35 | 100% Deterministic Evidence Traceability

1. **Under Risk Contributions Table**:
   - Click the **Inspect** button for finding `F-3e6ce30d9c2a6646` (`EG002`) or `F-66242556ba2742f9` (`EG003`).
2. **The Finding Detail Drawer opens**:
   - Point to the quantitative gap: Observed vs Baseline expectation.
   - Point to the **Supporting Evidence Records Table**:
     - Shows the exact source record ID, field, recorded value, and why it supports the finding.
   - Close the drawer.

---

## 1:35 – 1:55 | The Supervisory Review Queue (Triage Optimization)

1. **Click "Review Queue" (`/review-queue`) in the Sidebar**:
   - Point to the principle callout: **"Review Priority ≠ Risk Score"**.
   - *"Risk Score (53.22) measures cumulative entity severity; Review Priority (100.0) optimizes inspector time by putting systemic execution gaps at the top."*
2. **Show the Top Ranked Items**:
   - **Rank #1:** Finding `EG002` for `CSE-011` with Priority Score **`100.0 / 100`** (`HIGH PRIORITY`).
   - **Rank #2:** Entity recommendation for `CSE-011` with Priority Score **`80.1 / 100`**.
   - **Rank #3:** Unmonitored critical asset `AST-000444` (`NS002`) for `CSE-008`.

---

## 1:55 – 2:00 | Conclusion

1. **Final Wrap-Up**:
   - *"SENTRA turns complex, heterogeneous SOC submissions into explainable, traceable supervisory insight — enabling regulators and supervisors to know exactly who needs attention, why, and what concrete evidence supports it."*
