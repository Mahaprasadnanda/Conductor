import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class ServiceStatus(str, enum.Enum):
    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"
    IMPORTING = "Importing"
    DISABLED = "Disabled"

class ServiceAuthMode(str, enum.Enum):
    PUBLIC = "PUBLIC"
    JWT_REQUIRED = "JWT_REQUIRED"
    API_KEY_REQUIRED = "API_KEY_REQUIRED"
    DISABLED = "DISABLED"

class LoadBalancerStrategy(str, enum.Enum):
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_CONNECTIONS = "LEAST_CONNECTIONS"
    WEIGHTED_ROUND_ROBIN = "WEIGHTED_ROUND_ROBIN"
    RANDOM = "RANDOM"
    HEALTH_AWARE = "HEALTH_AWARE"

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(255), nullable=False, unique=True, index=True)
    base_url = Column(String(255), nullable=False)
    openapi_url = Column(String(255), nullable=True)
    health_check_path = Column(String(255), nullable=False, default="/health")
    authentication_mode = Column(Enum(ServiceAuthMode), default=ServiceAuthMode.JWT_REQUIRED, nullable=False)
    load_balancer_strategy = Column(Enum(LoadBalancerStrategy), default=LoadBalancerStrategy.ROUND_ROBIN, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.UNKNOWN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="services")
    endpoints = relationship("Endpoint", back_populates="service", cascade="all, delete-orphan")
    instances = relationship("ServiceInstance", back_populates="service", cascade="all, delete-orphan")

class ServiceInstance(Base):
    __tablename__ = "service_instances"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(String(255), nullable=False, unique=True, index=True)
    base_url = Column(String(255), nullable=False)
    weight = Column(Integer, default=1, nullable=False)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.UNKNOWN, nullable=False)
    active_connections = Column(Integer, default=0, nullable=False) # Fallback if redis is down
    priority = Column(Integer, default=0, nullable=False)
    zone = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    service = relationship("Service", back_populates="instances")
