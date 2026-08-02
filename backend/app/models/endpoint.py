from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False, index=True)
    operation_id = Column(String(255), nullable=True)
    summary = Column(String, nullable=True)
    description = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    response_defs = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    service = relationship("Service", back_populates="endpoints")
