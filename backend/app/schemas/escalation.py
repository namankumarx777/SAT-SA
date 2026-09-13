from datetime import datetime

from pydantic import BaseModel


class Escalation(BaseModel):
    id: str
    entity_id: str
    case_id: str

    created_at: datetime
    escalation_type: str