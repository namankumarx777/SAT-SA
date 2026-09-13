from __future__ import annotations

from app.analytics.rules.definitions import RULES, enabled_rules


def test_rule_registry_contains_only_initial_rules() -> None:
    assert set(RULES) == {"R001", "R002", "R003", "R004", "R005"}
    assert [rule.rule_id for rule in enabled_rules()] == ["R001", "R002", "R003", "R004", "R005"]
    for rule in enabled_rules():
        assert rule.description
        assert rule.version
        assert rule.thresholds
        assert rule.severity in {"Low", "Medium", "High", "Critical"}
