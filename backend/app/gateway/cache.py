from typing import Dict, Any
from app.models.service import Service, ServiceStatus
import structlog

log = structlog.get_logger()

class ServiceCache:
    _cache: Dict[str, dict[str, Any]] = {}

    @classmethod
    def set(cls, service_name: str, service_data: dict[str, Any]):
        cls._cache[service_name] = service_data
        
    @classmethod
    def get(cls, service_name: str) -> dict[str, Any] | None:
        return cls._cache.get(service_name)
        
    @classmethod
    def remove(cls, service_name: str):
        if service_name in cls._cache:
            del cls._cache[service_name]
            
    @classmethod
    def list_all(cls) -> list[dict[str, Any]]:
        return list(cls._cache.values())

    @classmethod
    def update_status(cls, service_name: str, status: ServiceStatus):
        if service_name in cls._cache:
            cls._cache[service_name]["status"] = status

    @classmethod
    def sync_from_db(cls, services: list[Service]):
        cls._cache.clear()
        for s in services:
            cls.set(s.service_name, {
                "service_id": s.id,
                "id": s.id,
                "project_id": s.project_id,
                "service_name": s.service_name,
                "base_url": str(s.base_url),
                "health_check_path": s.health_check_path,
                "authentication_mode": s.authentication_mode,
                "status": s.status
            })
        log.info("service_cache_synced", count=len(services))

service_cache = ServiceCache()
