from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.health import router as health_router
from app.api.v1.services import router as services_router
from app.api.v1.service_instances import router as service_instances_router
from app.api.v1.gateway import router as gateway_router
from app.api.v1.rate_limits import router as rate_limits_router
from app.api.v1.resilience import router as resilience_router
from app.api.v1.analytics import router as analytics_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(services_router, prefix="/services", tags=["services"])
router.include_router(service_instances_router, prefix="/service-instances", tags=["service_instances"])
router.include_router(gateway_router, prefix="/gateway", tags=["gateway"])
router.include_router(rate_limits_router, prefix="/rate-limits", tags=["rate_limits"])
router.include_router(resilience_router, prefix="/resilience", tags=["resilience"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(health_router, prefix="/health", tags=["health"])
