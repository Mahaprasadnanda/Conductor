from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """
    Exposes Prometheus metrics for internal scraping.
    """
    from app.gateway.metrics.prometheus import prometheus_manager
    from app.database.connection import async_session_maker
    from sqlalchemy.future import select
    from app.models.service import Service, ServiceInstance, ServiceStatus
    from prometheus_client import REGISTRY
    from app.core.logger import log
    import os
    
    log.info("MetricsEndpoint_Debug", 
             pid=os.getpid(),
             registry_id=id(REGISTRY), 
             manager_id=id(prometheus_manager),
             counter_id=id(prometheus_manager.gateway_requests_total))
    
    async with async_session_maker() as db:
        res = await db.execute(select(Service))
        prometheus_manager.gateway_services_registered.set(len(res.scalars().all()))
        
        res = await db.execute(select(ServiceInstance).where(ServiceInstance.status == ServiceStatus.HEALTHY))
        prometheus_manager.gateway_instances_registered.set(len(res.scalars().all()))
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
