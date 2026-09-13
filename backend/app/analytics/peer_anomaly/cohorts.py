from __future__ import annotations

import polars as pl

from app.analytics.peer_anomaly.models import Cohort

COHORT_COLUMNS = ["sector", "size", "criticality"]
MIN_COHORT_SIZE = 3


def cohort_key(row: dict[str, object]) -> str:
    return "|".join(str(row[column]) for column in COHORT_COLUMNS)


def build_cohorts(entity_features: pl.DataFrame, minimum_size: int = MIN_COHORT_SIZE) -> list[Cohort]:
    """Build deterministic structural cohorts without using activity volume."""
    cohorts: list[Cohort] = []
    for values, frame in entity_features.group_by(COHORT_COLUMNS, maintain_order=False):
        if len(values) == 3:
            sector, size, criticality = values
        else:
            sector, size, criticality = values[0]
        if frame.height < minimum_size:
            continue
        cohorts.append(Cohort(key=f"{sector}|{size}|{criticality}", sector=sector, size=size, criticality=criticality, entity_ids=sorted(frame["entity_id"].to_list())))
    return sorted(cohorts, key=lambda item: item.key)


def attach_cohort_keys(entity_features: pl.DataFrame) -> pl.DataFrame:
    return entity_features.with_columns(
        pl.concat_str([pl.col(column) for column in COHORT_COLUMNS], separator="|").alias("cohort_key")
    )
