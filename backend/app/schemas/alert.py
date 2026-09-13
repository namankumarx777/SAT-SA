from datetime import datetime

from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    entity_id: str
    asset_id: str

    timestamp: datetime
    severity: str
    source: str

    acknowledged_at: datetime | None = None
    closed_at: datetime | None = None

    status: str
    case_id: str | None = None