from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logger import setup_logger, log
from app.api.v1.router import router as v1_router
from app.api.v1.metrics import router as metrics_router
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    global_exception_handler,
    gateway_exception_handler,
)
from app.gateway.exceptions import GatewayException
from app.database.connection import redis_client, async_session_maker
from app.gateway.cache import service_cache
from app.gateway.registry import ServiceRegistry
from app.repositories.service import service_repo
from app.gateway.metrics.prometheus import prometheus_manager
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

import asyncio
from time import perf_counter

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# ============================================================
# Logger
# ============================================================

setup_logger()


# ============================================================
# Prometheus HTTP Metrics
# ============================================================

# Total HTTP requests.
#
# Because this is a Counter, Prometheus exposes it as:
#
# http_requests_total
#
# Labels:
#   method -> GET, POST, PUT, DELETE, etc.
#   path   -> FastAPI route path
#   status -> HTTP status code
#
http_requests_total = Counter(
    "http_requests",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)


# HTTP request latency.
#
# Prometheus will expose:
#
# http_request_duration_seconds_bucket
# http_request_duration_seconds_count
# http_request_duration_seconds_sum
#
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


# ============================================================
# Background Health Check
# ============================================================

async def background_health_check():
    while True:
        try:
            # Run service health checks
            await ServiceRegistry.run_health_checks()

            # ------------------------------------------------
            # Update registered services metric
            # ------------------------------------------------

            services_count = len(service_cache.list_all())

            prometheus_manager.gateway_services_registered.set(
                services_count
            )

            # ------------------------------------------------
            # Update healthy instances metric
            # ------------------------------------------------

            from app.models.service import ServiceInstance
            from sqlalchemy import select

            async with async_session_maker() as db:
                result = await db.execute(
                    select(ServiceInstance).where(
                        ServiceInstance.status == "Healthy"
                    )
                )

                instances_count = len(
                    result.scalars().all()
                )

            prometheus_manager.gateway_instances_registered.set(
                instances_count
            )

        except Exception as e:
            log.error(
                "health_check_loop_error",
                error=str(e),
            )

        await asyncio.sleep(10)


# ============================================================
# Prometheus HTTP Middleware
# ============================================================

class PrometheusHTTPMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = perf_counter()

        status_code = 500

        try:
            # Process request
            response = await call_next(request)

            status_code = response.status_code

            return response

        except Exception:
            # If an exception occurs, record it as HTTP 500
            status_code = 500
            raise

        finally:
            # ------------------------------------------------
            # Calculate request duration
            # ------------------------------------------------

            duration = perf_counter() - start_time

            method = request.method

            # ------------------------------------------------
            # Use FastAPI route template when available
            #
            # Example:
            #
            # /users/123
            # /users/456
            #
            # becomes:
            #
            # /users/{user_id}
            #
            # This prevents Prometheus from creating a
            # separate time series for every user ID.
            # ------------------------------------------------

            route = request.scope.get("route")

            if route is not None and hasattr(route, "path"):
                path = route.path
            else:
                path = request.url.path

            # ------------------------------------------------
            # Increment request counter
            # ------------------------------------------------

            http_requests_total.labels(
                method=method,
                path=path,
                status=str(status_code),
            ).inc()

            # ------------------------------------------------
            # Record request duration
            # ------------------------------------------------

            http_request_duration_seconds.labels(
                method=method,
                path=path,
            ).observe(duration)


# ============================================================
# FastAPI Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    log.info(
        "startup",
        message="Starting Conductor Backend",
    )

    # --------------------------------------------------------
    # Initialize service cache from database
    # --------------------------------------------------------

    async with async_session_maker() as db:

        from sqlalchemy import select
        from app.models.service import Service

        result = await db.execute(
            select(Service)
        )

        service_cache.sync_from_db(
            list(result.scalars().all())
        )

    # --------------------------------------------------------
    # Start background health checks
    # --------------------------------------------------------

    health_task = asyncio.create_task(
        background_health_check()
    )

    yield

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    log.info(
        "shutdown",
        message="Shutting down Conductor Backend",
    )

    health_task.cancel()

    await redis_client.aclose()


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="Conductor API",
    description=(
        "Intelligent Traffic Orchestration Platform "
        "for Cloud-Native APIs"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# CORS Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Exception Handlers
# ============================================================

app.add_exception_handler(
    GatewayException,
    gateway_exception_handler,
)

app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)


# ============================================================
# Host Routing Middleware
# ============================================================

class HostRoutingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        host = request.headers.get(
            "host",
            "",
        )

        if (
            ".api.localhost" in host
            or ".api.conductor.dev" in host
        ):

            subdomain = host.split(".api.")[0]

            original_path = request.scope.get(
                "path",
                "",
            )

            # Ensure path starts with /
            if not original_path.startswith("/"):
                original_path = "/" + original_path

            # Prevent double-prefixing
            if (
                not original_path.startswith(
                    f"/api/v1/gateway/{subdomain}"
                )
                and not original_path.startswith(
                    "/api/v1/gateway/"
                )
            ):

                request.scope["path"] = (
                    f"/api/v1/gateway/"
                    f"{subdomain}"
                    f"{original_path}"
                )

        return await call_next(request)


# ============================================================
# Register Middleware
# ============================================================

app.add_middleware(
    HostRoutingMiddleware
)

app.add_middleware(
    PrometheusHTTPMiddleware
)


# ============================================================
# Routers
# ============================================================

app.include_router(
    v1_router,
    prefix="/api/v1",
)

app.include_router(
    metrics_router
)