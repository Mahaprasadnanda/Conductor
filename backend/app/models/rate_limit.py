import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class RateLimitAlgorithm(str, enum.Enum):
    SLIDING_WINDOW_LOG = "SLIDING_WINDOW_LOG"
    SLIDING_WINDOW_COUNTER = "SLIDING_WINDOW_COUNTER"
    TOKEN_BUCKET = "TOKEN_BUCKET"
    FIXED_WINDOW = "FIXED_WINDOW"
    ADAPTIVE = "ADAPTIVE"

class RateLimitPolicy(Base):
    __tablename__ = "rate_limit_policies"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=True)
    endpoint_path = Column(String(255), nullable=True)
    limit = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    algorithm = Column(Enum(RateLimitAlgorithm, name="ratelimitalgorithm"), nullable=False, default=RateLimitAlgorithm.SLIDING_WINDOW_LOG)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    service = relationship("Service", backref="rate_limits")
