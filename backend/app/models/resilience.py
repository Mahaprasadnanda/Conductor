from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class ResiliencePolicy(Base):
    __tablename__ = "resilience_policies"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), unique=True, nullable=False)
    
    # Circuit Breaker config
    failure_threshold = Column(Integer, default=5, nullable=False)
    recovery_timeout = Column(Integer, default=60, nullable=False)
    half_open_requests = Column(Integer, default=2, nullable=False)
    
    # Retry config
    retry_attempts = Column(Integer, default=3, nullable=False)
    
    # Timeout config
    request_timeout = Column(Integer, default=30, nullable=False)
    
    # Fallback config
    fallback_enabled = Column(Boolean, default=False, nullable=False)
    fallback_response = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    service = relationship("Service", backref="resilience_policy")
