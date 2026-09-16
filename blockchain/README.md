# SENTRA Hyperledger Fabric Blockchain Integrity Layer

## Overview
SENTRA integrates a local, permissioned **Hyperledger Fabric** ledger to establish **tamper-evident cryptographic provenance** for CSE telemetry datasets, supervisory analytical findings, and linked evidence packages.

Raw SOC data remains strictly local in Parquet files. Only deterministic SHA-256 digests and identity metadata are committed on-chain.

## Directory Structure
```text
blockchain/
├── chaincode/
│   └── SENTRA-integrity/
│       ├── integrity.go        # Go Smart Contract (Fabric v2 contract API)
│       ├── integrity_test.go   # Go Unit Tests
│       └── go.mod              # Go Module Definition
├── network/
│   ├── docker-compose-test-net.yaml # Orderer + CSE-A Peer + CSE-B Peer
│   └── connection-org1.json         # Fabric Gateway Connection Profile
├── scripts/
│   ├── start.sh / start.ps1    # Start local Fabric test network
│   ├── stop.sh / stop.ps1      # Stop and tear down network
│   ├── status.sh / status.ps1  # Check running containers
│   └── tamper_demo.py          # End-to-end controlled tamper & verify demo
└── README.md
```

## Running the Chaincode Unit Tests
```bash
cd blockchain/chaincode/SENTRA-integrity
go test -v ./...
```
