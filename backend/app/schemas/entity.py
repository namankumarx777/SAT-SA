from datetime import datetime

from pydantic import BaseModel


class Entity(BaseModel):
    id: str
    name: str
    sector: str
    size: str
    criticality: str
    created_at: datetime