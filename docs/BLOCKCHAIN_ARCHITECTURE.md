# SENTRA Blockchain Integrity & Provenance Architecture

## 1. Executive Summary & Purpose

The SENTRA Hyperledger Fabric integration establishes a **tamper-evident cryptographic provenance layer** for cybersecurity telemetry datasets, supervisory analytical findings, and linked evidence packages.

### The Core Problem Solved:
> In supervisory cybersecurity oversight, an adversary or non-compliant entity might attempt to retroactively modify telemetry records or refute automated supervisory findings. Can SENTRA prove that a submitted cybersecurity dataset, analytical finding, and evidence package has not been altered after being recorded?

```text
Cybersecurity Analytics + Blockchain Integrity = Trustworthy Supervisory Evidence
```

---

## 2. Architectural Separation: Off-Chain Telemetry vs. On-Chain Digests

A critical tenet of SENTRA is **never storing raw SOC data directly on the ledger**.

```text
┌─────────────────────────────────────────────────────────┐
│                     LOCAL STORAGE                       │
│  (Parquet Files / DuckDB / Polars In-Memory Analytics)  │
│  - 10,000+ Raw SIEM / EDR Alerts                        │
│  - Incident Case Investigation Notes                    │
│  - Asset Inventories & Vulnerability Scans              │
│  - Full Multi-Phase Finding Evidence Chains             │
└────────────────────────────┬────────────────────────────┘
                             │
                  Deterministic SHA-256
                    Canonical Hashing
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              HYPERLEDGER FABRIC LEDGER                  │
│       (Permissioned Consensus / World State)            │
│  - Cryptographic SHA-256 Digest                         │
│  - Entity ID & Submission Period                        │
│  - Detector / Rule Reference                            │
│  - Version Number & Timestamp                           │
│  - Transaction ID & Immutable State History             │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Network Topology & Participants

The prototype operates as a local, permissioned Hyperledger Fabric network structured around supervisory oversight:

```text
                       SENTRA Supervisor
                     (Ordering Service Node)
                       localhost:7050
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Peer 0 (CSE-A)                Peer 0 (CSE-B)
       (Org1MSP / Peer)              (Org2MSP / Peer)
        localhost:7051                localhost:9051
```

- **Dedicated Channel**: `SENTRA-channel`
- **Smart Contract (Chaincode)**: `SENTRA-integrity` (Fabric v2 Contract API in Go)

---

## 4. Ledger Data Model & Schemas

### A. Submission Commitment Record (`SUBMISSION`)
```json
{
  "recordId": "SUB-CSE-011-2026-Q2",
  "recordType": "SUBMISSION",
  "entityId": "CSE-011",
  "period": "2026-Q2",
  "contentHash": "e3042c699a8470bea2ec3c1f457147ebc2c572225882a9602f7e5020a447129e",
  "manifestHash": "61a9c3948e...",
  "createdAt": "2026-09-16T10:00:00Z",
  "registeredBy": "SENTRA",
  "version": 1
}
```

### B. Finding Commitment Record (`FINDING`)
```json
{
  "recordId": "F-EG002-CSE-011",
  "recordType": "FINDING",
  "entityId": "CSE-011",
  "findingHash": "f9662a5c9c8438ec39c7447011078c523f331037c962693943f06a284b9c379e",
  "sourcePhase": "phase6",
  "detectorId": "EG002",
  "createdAt": "2026-09-16T10:05:00Z",
  "registeredBy": "SENTRA",
  "version": 1
}
```

### C. Evidence Commitment Record (`EVIDENCE`)
```json
{
  "recordId": "EVD-ESC-9081",
  "recordType": "EVIDENCE",
  "entityId": "CSE-011",
  "findingId": "F-EG002-CSE-011",
  "contentHash": "6be580f7ad9373a677e976e105a136fd13240cd00369504d36cac0fc4ef73759",
  "createdAt": "2026-09-16T10:06:00Z",
  "registeredBy": "SENTRA",
  "version": 1
}
```

---

## 5. Deterministic Hashing Methodology

To prevent byte-level drift between platforms and runtime environments:
1. **Canonical JSON Serialization**: Keys are sorted lexicographically, whitespace separators stripped (`("," , ":")`), and strings encoded in UTF-8.
2. **Submission Ordering**: Parquet datasets are hashed in fixed sequence:
   - `entities.parquet` → `assets.parquet` → `alerts.parquet` → `cases.parquet` → `escalations.parquet` → `manifest.json`.
   - The combined digest represents the full submission partition digest.
3. **Finding Normalization**: Extracted fields (`entity_id`, `expected_value`, `finding_id`, `metric_name`, `observed_value`, `rationale`, `rule_id`, `severity`).
4. **Evidence Normalization**: Extracted fields (`entity_id`, `field`, `finding_id`, `reason`, `source_id`, `source_type`, `value`).

---

## 6. Integrity Verification States

The verification API responds with four distinct states:
- `VERIFIED`: Live computed SHA-256 digest identically matches the on-chain ledger commitment.
- `MISMATCH`: Live computed SHA-256 digest differs from ledger commitment (tampering or unauthorized modification detected).
- `NOT_REGISTERED`: No commitment exists on the ledger for the requested identifier.
- `UNAVAILABLE`: Hyperledger Fabric network is unreachable; core analytics proceed without interruption.

> **Supervisory Rule**: Blockchain verification answers cryptographic consistency; it **never** alters risk scores, severity levels, or dimension weights.
