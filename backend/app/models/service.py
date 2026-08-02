import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class ServiceStatus(str, enum.Enum):
    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"
    IMPORTING = "Importing"

class ServiceAuthMode(str, enum.Enum):
    PUBLIC = "PUBLIC"
    JWT_REQUIRED = "JWT_REQUIRED"
    API_KEY_REQUIRED = "API_KEY_REQUIRED"
    DISABLED = "DISABLED"

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(255), nullable=False, unique=True, index=True)
    base_url = Column(String(255), nullable=False)
    openapi_url = Column(String(255), nullable=True)
    health_check_path = Column(String(255), nullable=False, default="/health")
    authentication_mode = Column(Enum(ServiceAuthMode), default=ServiceAuthMode.JWT_REQUIRED, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.UNKNOWN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="services")
    endpoints = relationship("Endpoint", back_populates="service", cascade="all, delete-orphan")
