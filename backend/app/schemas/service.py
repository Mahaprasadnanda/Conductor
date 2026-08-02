from pydantic import BaseModel, ConfigDict, HttpUrl
from typing import Optional, Any
from datetime import datetime
from app.models.service import ServiceStatus, ServiceAuthMode

class ServiceBase(BaseModel):
    service_name: str
    base_url: HttpUrl | str
    openapi_url: Optional[HttpUrl | str] = None
    health_check_path: str = "/health"
    authentication_mode: ServiceAuthMode = ServiceAuthMode.JWT_REQUIRED
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    service_name: Optional[str] = None
    base_url: Optional[HttpUrl | str] = None
    openapi_url: Optional[HttpUrl | str] = None
    health_check_path: Optional[str] = None
    authentication_mode: Optional[ServiceAuthMode] = None
    description: Optional[str] = None
    status: Optional[ServiceStatus] = None

class ServiceResponse(ServiceBase):
    id: int
    project_id: int
    status: ServiceStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
