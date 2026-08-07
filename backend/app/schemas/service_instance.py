from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.service import ServiceStatus
import uuid

class ServiceInstanceBase(BaseModel):
    instance_id: Optional[str] = None
    base_url: str = Field(..., max_length=255)
    weight: int = Field(1, ge=1, description="Weight for Weighted Round Robin")
    status: ServiceStatus = Field(default=ServiceStatus.UNKNOWN)
    priority: int = Field(0, description="Priority for failover routing")
    zone: Optional[str] = Field(None, max_length=255)

    @field_validator("instance_id", mode="before")
    def set_instance_id(cls, v):
        return v or str(uuid.uuid4())

class ServiceInstanceCreate(ServiceInstanceBase):
    service_id: int

class ServiceInstanceUpdate(BaseModel):
    base_url: Optional[str] = Field(None, max_length=255)
    weight: Optional[int] = Field(None, ge=1)
    status: Optional[ServiceStatus] = None
    priority: Optional[int] = None
    zone: Optional[str] = Field(None, max_length=255)

class ServiceInstanceResponse(ServiceInstanceBase):
    id: int
    service_id: int
    active_connections: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
