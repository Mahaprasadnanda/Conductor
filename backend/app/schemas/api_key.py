from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ApiKeyBase(BaseModel):
    name: str

class ApiKeyCreate(ApiKeyBase):
    project_id: int

class ApiKeyResponse(ApiKeyBase):
    id: int
    project_id: int
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ApiKeyReveal(ApiKeyResponse):
    raw_key: str
