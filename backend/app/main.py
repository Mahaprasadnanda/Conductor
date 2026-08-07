from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logger import setup_logger, log
from app.api.v1.router import router as v1_router
from app.api.v1.metrics import router as metrics_router
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler, gateway_exception_handler
from app.gateway.exceptions import GatewayException
from app.database.connection import redis_client, async_session_maker
from app.gateway.cache import service_cache
from app.gateway.registry import ServiceRegistry
from app.repositories.service import service_repo
from app.gateway.metrics.prometheus import prometheus_manager
import asyncio

setup_logger()

async def background_health_check():
    while True:
        try:
            await ServiceRegistry.run_health_checks()
            
            # Update metrics gauges periodically
            services_count = len(service_cache.list_all())
            prometheus_manager.gateway_services_registered.set(services_count)
            
            from app.models.service import ServiceInstance
            from sqlalchemy import select
            async with async_session_maker() as db:
                result = await db.execute(select(ServiceInstance).where(ServiceInstance.status == "Healthy"))
                instances_count = len(result.scalars().all())
            prometheus_manager.gateway_instances_registered.set(instances_count)
            
        except Exception as e:
            log.error("health_check_loop_error", error=str(e))
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", message="Starting Conductor Backend")
    
    # Initialize cache
    async with async_session_maker() as db:
        from sqlalchemy import select
        from app.models.service import Service
        result = await db.execute(select(Service))
        service_cache.sync_from_db(list(result.scalars().all()))
        
    # Start health checks
    health_task = asyncio.create_task(background_health_check())
    
    yield
    
    log.info("shutdown", message="Shutting down Conductor Backend")
    health_task.cancel()
    await redis_client.aclose()

app = FastAPI(
    title="Conductor API",
    description="Intelligent Traffic Orchestration Platform for Cloud-Native APIs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_exception_handler(GatewayException, gateway_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(metrics_router)

