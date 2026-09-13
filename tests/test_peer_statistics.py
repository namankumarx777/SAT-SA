from __future__ import annotations

from app.analytics.peer_anomaly.anomaly import prepare_anomaly_matrix
from app.analytics.peer_anomaly.statistics import deviation

import polars as pl


def test_deviation_and_anomaly_matrix_remove_constants_and_impute_median() -> None:
    frame = pl.DataFrame({"entity_id": ["E1", "E2", "E3"], "constant": [1.0, 1.0, 1.0], "alerts_per_asset": [1.0, None, 3.0]})
    matrix, features = prepare_anomaly_matrix(frame)
    assert features == ["alerts_per_asset"]
    assert matrix["alerts_per_asset"].null_count() == 0
    assert deviation(0.2, 0.5) == (0.3, 0.6)
