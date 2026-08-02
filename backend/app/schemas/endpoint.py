from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class EndpointBase(BaseModel):
    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    request_body: Optional[dict[str, Any]] = None
    response_defs: Optional[dict[str, Any]] = None
    is_active: bool = True

class EndpointCreate(EndpointBase):
    pass

class EndpointUpdate(BaseModel):
    path: Optional[str] = None
    method: Optional[str] = None
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    request_body: Optional[dict[str, Any]] = None
    response_defs: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None

class EndpointResponse(EndpointBase):
    id: int
    service_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
