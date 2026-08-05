from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ResiliencePolicyBase(BaseModel):
    service_id: int
    failure_threshold: int = Field(default=5, ge=1)
    recovery_timeout: int = Field(default=60, ge=1)
    half_open_requests: int = Field(default=2, ge=1)
    retry_attempts: int = Field(default=3, ge=0)
    request_timeout: int = Field(default=30, ge=1)
    fallback_enabled: bool = Field(default=False)
    fallback_response: Optional[Dict[str, Any]] = None

class ResiliencePolicyCreate(ResiliencePolicyBase):
    pass

class ResiliencePolicyUpdate(BaseModel):
    failure_threshold: Optional[int] = Field(None, ge=1)
    recovery_timeout: Optional[int] = Field(None, ge=1)
    half_open_requests: Optional[int] = Field(None, ge=1)
    retry_attempts: Optional[int] = Field(None, ge=0)
    request_timeout: Optional[int] = Field(None, ge=1)
    fallback_enabled: Optional[bool] = None
    fallback_response: Optional[Dict[str, Any]] = None

class ResiliencePolicyResponse(ResiliencePolicyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
