# SENTRA Hyperledger Fabric Local Setup & Operation Guide

## Prerequisites & Environment

- **Operating System**: Windows 11 / WSL2 (Ubuntu 22.04+) or Native Windows Environment
- **Docker Desktop**: Docker Engine v24+ / Docker Compose v2+
- **Go**: Version 1.22+ (`go.mod` configured with Fabric Contract API v2)
- **Python**: Version 3.10+ (Existing backend virtual environment)

---

## 1. Directory Structure

```text
blockchain/
├── chaincode/
│   └── SENTRA-integrity/
│       ├── integrity.go        # Smart Contract implementation
│       ├── integrity_test.go   # Go unit test suite
│       └── go.mod              # Go dependencies
├── network/
│   ├── docker-compose-test-net.yaml # Orderer + Peer 0 (CSE-A) + Peer 0 (CSE-B)
│   └── connection-org1.json         # Client gateway connection profile
├── scripts/
│   ├── start.sh / start.ps1    # Startup scripts
│   ├── stop.sh / stop.ps1      # Teardown scripts
│   ├── status.sh / status.ps1  # Inspection scripts
│   └── tamper_demo.py          # Interactive tamper demonstration
└── README.md
```

---

## 2. Chaincode Verification (Go Test)

To compile and verify the Go smart contract unit tests:

```powershell
cd blockchain\chaincode\SENTRA-integrity
& "C:\Program Files\Go\bin\go.exe" test -v ./...
```

Output:
```text
=== RUN   TestRegisterAndVerifySubmission
--- PASS: TestRegisterAndVerifySubmission (0.00s)
=== RUN   TestRegisterFindingAndEvidence
--- PASS: TestRegisterFindingAndEvidence (0.00s)
PASS
ok      SENTRA-integrity        0.275s
```

---

## 3. Network Lifecycle Commands

### Starting the Local Fabric Network
- **Linux / WSL2**:
  ```bash
  bash blockchain/scripts/start.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\blockchain\scripts\start.ps1
  ```

### Checking Network Status
- **Linux / WSL2**:
  ```bash
  bash blockchain/scripts/status.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\blockchain\scripts\status.ps1
  ```

### Stopping the Network
- **Linux / WSL2**:
  ```bash
  bash blockchain/scripts/stop.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\blockchain\scripts\stop.ps1
  ```

---

## 4. Running the Backend & Frontend

### Backend:
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Frontend:
```powershell
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

---

## 5. Running the Tamper & Verification Demo
```powershell
.\backend\.venv\Scripts\python.exe blockchain\scripts\tamper_demo.py
```
