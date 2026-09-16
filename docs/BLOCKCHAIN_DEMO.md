# SENTRA Smart India Hackathon (SIH) Blockchain Demo Script

## Duration: ~30–45 Seconds

### Context & Narrative
> "SENTRA does not just identify operational cyber posture weaknesses across CSEs—it establishes tamper-evident cryptographic provenance so that evidence presented during supervisory review cannot be disputed or retroactively manipulated."

---

## Live Demonstration Sequence

| Step | Action | UI / CLI State | Spoken Narrative |
| :--- | :--- | :--- | :--- |
| **1** | Open **CSE-011 Assessment** | Risk Score: `53.22` (HIGH), Top Deficiency: `Investigation Effort` | *"We inspect CSE-011, flagged for severe investigation and escalation delays across Q2."* |
| **2** | Open **EG002 Finding** in Inspector Drawer | Finding Detail Drawer slides open | *"Opening detector EG002, we see evidence showing a 74.5-hour delay between alert escalation and ticket creation."* |
| **3** | Click **"Verify Integrity"** | Status changes to `✓ VERIFIED` (Green), Local & Ledger SHA-256 digests match | *"With one click, SENTRA queries our local Hyperledger Fabric ledger (`SENTRA-channel`). The SHA-256 cryptographic digest matches the on-chain commitment exactly."* |
| **4** | Run Controlled Tamper in CLI | CLI executes `tamper_demo.py` step 3 | *"Suppose an adversary or compromised operator attempts to modify this evidence to falsely show a 2.0-hour delay."* |
| **5** | Click **"Verify Integrity"** again | Status changes to `⚠ MISMATCH` (Red) with alert | *"Instantly, SENTRA detects an integrity mismatch against the immutable ledger and warns the supervisor."* |
| **6** | Restore Record & Re-Verify | Status restores to `✓ VERIFIED` | *"Restoring authentic data re-establishes cryptographic verification. Off-chain data efficiency combined with on-chain integrity guarantees trustworthy supervisory oversight."* |

---

## Executing the Standalone Script
```powershell
backend\.venv\Scripts\python.exe blockchain\scripts\tamper_demo.py
```
