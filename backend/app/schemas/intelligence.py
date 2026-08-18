from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class Anomaly(BaseModel):
    anomaly_type: str = Field(..., description="e.g., Traffic Spike, Error Spike, Latency Spike")
    severity: SeverityEnum
    service_name: Optional[str] = None
    instance_id: Optional[str] = None
    current_value: float
    baseline_value: float
    deviation: str = Field(..., description="e.g., '+50%' or '10x'")
    detected_at: str = Field(..., description="ISO 8601 timestamp")
    explanation: str
    recommendation: str

class Recommendation(BaseModel):
    title: str
    severity: SeverityEnum
    reason: str
    evidence: str
    recommended_action: str
    affected_service: Optional[str] = None
    affected_instance: Optional[str] = None

class IntelligenceOverview(BaseModel):
    status: str = Field(..., description="Overall system intelligence status: HEALTHY, DEGRADED, CRITICAL")
    active_anomaly_count: int
    recent_anomalies: List[Anomaly] = []
    recommendations: List[Recommendation] = []
