from __future__ import annotations

from app.analytics.negative_space.definitions import DETECTORS, enabled_detectors


def test_negative_space_registry_and_deferrals() -> None:
    assert set(DETECTORS) == {"NS001", "NS002", "NS003", "NS004", "NS005", "NS006"}
    assert {item.detector_id for item in enabled_detectors()} == {"NS001", "NS002", "NS003", "NS004", "NS005"}
    assert DETECTORS["NS006"].deferred_reason
    for detector in DETECTORS.values():
        assert detector.expectation_method
        assert detector.data_requirements
