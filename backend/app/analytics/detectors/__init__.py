"""Shared detector core used by every supervisory analysis phase.

Houses the canonical Finding/Evidence models, deterministic evidence factories,
Phase 4 feature-bundle loading, and the deterministic ordering/serialization
helpers so downstream phases do not depend on the Phase 5 rule package.
"""