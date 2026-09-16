from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.models import SubmissionCommitment
from app.main import app

client = TestClient(app)


def test_blockchain_status_endpoint():
    response = client.get("/blockchain/status")
    assert response.status_code == 200
    data = response.json()
    assert "channel" in data
    assert "chaincode" in data
    assert data["status"] in ("connected", "unavailable")


def test_blockchain_registration_and_verification_flow():
    # Setup test submission directory
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        (dir_path / "alerts.parquet").write_bytes(b"alerts_test_data")
        (dir_path / "manifest.json").write_text('{"submission": "SUB-TEST-001"}')

        # Register submission
        reg_resp = client.post(
            "/blockchain/submissions/SUB-TEST-001/register",
            json={
                "entity_id": "CSE-011",
                "period": "2026-Q2",
                "data_directory": str(dir_path),
            },
        )
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert reg_data["status"] == "registered"
        assert "tx_id" in reg_data

        # Lookup ledger record
        get_resp = client.get("/blockchain/records/SUB-TEST-001")
        assert get_resp.status_code == 200
        rec_data = get_resp.json()
        assert rec_data["recordId"] == "SUB-TEST-001"
        assert rec_data["entityId"] == "CSE-011"

        # Verify record matches
        content_hash = rec_data["contentHash"]
        verify_resp = client.post(
            "/blockchain/records/SUB-TEST-001/verify",
            json={"expected_hash": content_hash},
        )
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["status"] == "VERIFIED"

        # Verify mismatch when hash is tampered
        verify_mismatch = client.post(
            "/blockchain/records/SUB-TEST-001/verify",
            json={"expected_hash": "tampered_fake_hash_123"},
        )
        assert verify_mismatch.status_code == 200
        assert verify_mismatch.json()["status"] == "MISMATCH"

        # Check history
        hist_resp = client.get("/blockchain/records/SUB-TEST-001/history")
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 1
        assert history[0]["txId"] == reg_data["tx_id"]
