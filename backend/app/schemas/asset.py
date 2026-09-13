from pydantic import BaseModel


class Asset(BaseModel):
    id: str
    entity_id: str
    asset_type: str
    criticality: str
    expected_monitoring: bool
    monitoring_source: str | None = None