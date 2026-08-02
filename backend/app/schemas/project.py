from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
