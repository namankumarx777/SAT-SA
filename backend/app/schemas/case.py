from datetime import datetime

from pydantic import BaseModel


class Case(BaseModel):
    id: str
    entity_id: str
    alert_id: str

    opened_at: datetime
    closed_at: datetime | None = None

    investigation_text: str
    disposition: str

    escalated: bool
    remediation_recorded: bool