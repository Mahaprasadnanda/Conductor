from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.rate_limit import RateLimitAlgorithm

class RateLimitPolicyBase(BaseModel):
    service_id: Optional[int] = None
    endpoint_path: Optional[str] = None
    limit: int
    window_seconds: int
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW_LOG
    enabled: bool = True

class RateLimitPolicyCreate(RateLimitPolicyBase):
    pass

class RateLimitPolicyUpdate(BaseModel):
    service_id: Optional[int] = None
    endpoint_path: Optional[str] = None
    limit: Optional[int] = None
    window_seconds: Optional[int] = None
    algorithm: Optional[RateLimitAlgorithm] = None
    enabled: Optional[bool] = None

from pydantic import ConfigDict

class RateLimitPolicyResponse(RateLimitPolicyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
