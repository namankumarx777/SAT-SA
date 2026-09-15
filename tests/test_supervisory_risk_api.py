from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_entities_and_queue(client: TestClient) -> None:
    # 1. GET /analytics/supervisory-risk/entities
    resp_entities = client.get("/analytics/supervisory-risk/entities")
    assert resp_entities.status_code == 200
    entities = resp_entities.json()
    assert len(entities) == 12
    assert any(e["entity_id"] == "CSE-001" for e in entities)

    # 2. GET /analytics/supervisory-risk/entities/CSE-011
    resp_entity = client.get("/analytics/supervisory-risk/entities/CSE-011")
    assert resp_entity.status_code == 200
    entity_data = resp_entity.json()
    assert entity_data["entity_id"] == "CSE-011"
    assert "overall_score" in entity_data
    assert "risk_band" in entity_data

    # 3. GET /analytics/supervisory-risk/contributions/CSE-011
    resp_contribs = client.get("/analytics/supervisory-risk/contributions/CSE-011")
    assert resp_contribs.status_code == 200
    contribs = resp_contribs.json()
    assert len(contribs) > 0

    # 4. GET /analytics/supervisory-risk/review-queue
    resp_queue = client.get("/analytics/supervisory-risk/review-queue")
    assert resp_queue.status_code == 200
    queue = resp_queue.json()
    assert len(queue) > 0
    first_item = queue[0]
    assert first_item["rank"] == 1
    assert "priority" in first_item

    # 5. GET /analytics/supervisory-risk/review-queue/{record_id}
    rec_id = first_item["record_id"]
    resp_item = client.get(f"/analytics/supervisory-risk/review-queue/{rec_id}")
    assert resp_item.status_code == 200
    assert resp_item.json()["record_id"] == rec_id

    # 6. GET /analytics/supervisory-risk/manifest
    resp_manifest = client.get("/analytics/supervisory-risk/manifest")
    assert resp_manifest.status_code == 200
    manifest_data = resp_manifest.json()
    assert "dimensions" in manifest_data
    assert "an001_configuration" in manifest_data
    assert "dimension_assessability_rule" in manifest_data

    # 7. GET /analytics/supervisory-risk/findings/{finding_id}
    resp_finding = client.get("/analytics/supervisory-risk/findings/F-66242556ba2742f9")
    assert resp_finding.status_code == 200
    finding_data = resp_finding.json()
    assert "finding" in finding_data
    assert "evidence" in finding_data
    assert finding_data["finding"]["rule_id"] == "EG003"


def test_api_not_found(client: TestClient) -> None:
    resp = client.get("/analytics/supervisory-risk/entities/CSE-NONEXISTENT")
    assert resp.status_code == 404

    resp_f = client.get("/analytics/supervisory-risk/findings/NONEXISTENT_FINDING")
    assert resp_f.status_code == 404
