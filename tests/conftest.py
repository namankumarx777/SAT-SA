from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.data.generate_synthetic import generate_dataset  # noqa: E402


@pytest.fixture(scope="session")
def phase2_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("phase2")
    generate_dataset(12, 500, 42, output)
    return output
