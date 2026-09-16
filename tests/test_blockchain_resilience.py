from __future__ import annotations

from fastapi.testclient import TestClient

from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.models import IntegrityState
from app.main import app

client = TestClient(app)


def test_blockchain_network_offline_graceful_handling():
    fabric_client = get_fabric_client()
    try:
        # Simulate network offline
        fabric_client.set_online(False)

        # Status endpoint should return unavailable, not error out
        status_resp = client.get("/blockchain/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "unavailable"
        assert status_resp.json()["is_connected"] is False

        # Verification endpoint should return UNAVAILABLE status, not crash or 500
        verify_resp = client.post(
            "/blockchain/records/ANY_RECORD/verify",
            json={"expected_hash": "sample_hash"},
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["status"] == IntegrityState.UNAVAILABLE.value

        # Health endpoint of main application should remain unaffected
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

    finally:
        # Restore online state
        fabric_client.set_online(True)
