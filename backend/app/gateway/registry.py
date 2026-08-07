import httpx
import asyncio
from app.gateway.cache import service_cache
from app.models.service import ServiceStatus
from app.database.connection import async_session_maker
from app.repositories.service import service_repo
import structlog

log = structlog.get_logger()

class ServiceRegistry:
    @staticmethod
    async def check_health(service_data: dict) -> tuple[str, ServiceStatus]:
        service_name = service_data["service_name"]
        base_url = service_data["base_url"].rstrip("/")
        health_path = service_data.get("health_check_path", "/health").lstrip("/")
        
        url = f"{base_url}/{health_path}"
        
        # If currently importing, do not check health
        if service_data.get("status") == ServiceStatus.IMPORTING:
            return service_name, ServiceStatus.IMPORTING

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Use stream to immediately get headers and avoid ReadTimeout on hanging connections
                async with client.stream("GET", url) as response:
                    log.info("health_check_response", url=url, status=response.status_code)
                    if 200 <= response.status_code < 300:
                        try:
                            # Attempt to read body with a short timeout to check for explicit {"status": "unhealthy"}
                            await response.aread()
                            data = response.json()
                            if isinstance(data, dict):
                                status_val = str(data.get("status", "")).lower()
                                if status_val in ["unhealthy", "down", "error", "fail"]:
                                    return service_name, ServiceStatus.UNHEALTHY
                        except Exception:
                            pass # Ignore JSON parsing or body read errors, 200 OK is enough
                            
                        return service_name, ServiceStatus.HEALTHY
                return service_name, ServiceStatus.UNHEALTHY
            except Exception as e:
                log.error("health_check_exception", url=url, error=str(e))
                return service_name, ServiceStatus.UNHEALTHY

    @staticmethod
    async def run_health_checks():
        services = service_cache.list_all()
        if not services:
            return
            
        tasks = [ServiceRegistry.check_health(s) for s in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # We need a DB session to persist health status updates
        async with async_session_maker() as db:
            for result in results:
                if isinstance(result, Exception):
                    continue
                service_name, new_status = result
                
                # Check if it changed
                current_data = service_cache.get(service_name)
                if current_data and current_data.get("status") != new_status:
                    current_data["status"] = new_status
                    service_cache.update_status(service_name, new_status)
                    # Persist to DB
                    db_service = await service_repo.get_by_name(db, service_name=service_name)
                    if db_service:
                        db_service.status = new_status
                        db.add(db_service)
                        
            await db.commit()
