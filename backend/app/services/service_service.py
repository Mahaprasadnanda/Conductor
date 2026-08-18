from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.service import service_repo
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.models.service import Service
from app.gateway.cache import service_cache

class ServiceService:
    @staticmethod
    async def create_service(db: AsyncSession, service_in: ServiceCreate, project_id: int) -> Service:
        existing = await service_repo.get_by_name(db, service_name=service_in.service_name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service name already exists")
            
        service_data = service_in.model_dump()
        service_data["base_url"] = str(service_data["base_url"]).rstrip("/")
        if service_data.get("openapi_url"):
            service_data["openapi_url"] = str(service_data["openapi_url"])
            
        db_service = Service(**service_data, project_id=project_id)
        db.add(db_service)
        await db.commit()
        await db.refresh(db_service)
        
        service_cache.set(db_service.service_name, {
            "id": db_service.id,
            "project_id": db_service.project_id,
            "service_name": db_service.service_name,
            "base_url": db_service.base_url,
            "health_check_path": db_service.health_check_path,
            "authentication_mode": db_service.authentication_mode,
            "load_balancer_strategy": db_service.load_balancer_strategy.value if hasattr(db_service.load_balancer_strategy, "value") else db_service.load_balancer_strategy,
            "status": db_service.status
        })
        return db_service

    @staticmethod
    async def get_service(db: AsyncSession, service_id: int, project_id: int) -> Service:
        service = await service_repo.get(db, id=service_id)
        if not service or service.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        return service

    @staticmethod
    async def list_services(db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> list[Service]:
        return await service_repo.get_multi_by_project(db, project_id=project_id, skip=skip, limit=limit)

    @staticmethod
    async def update_service(db: AsyncSession, service_id: int, service_in: ServiceUpdate, project_id: int) -> Service:
        service = await ServiceService.get_service(db, service_id, project_id)
        
        # Pre-process base_url to string and strip trailing slash if present
        if service_in.base_url:
            service_in.base_url = str(service_in.base_url).rstrip("/")
            
        updated_service = await service_repo.update(db, db_obj=service, obj_in=service_in)
        
        service_cache.set(updated_service.service_name, {
            "id": updated_service.id,
            "project_id": updated_service.project_id,
            "service_name": updated_service.service_name,
            "base_url": updated_service.base_url,
            "health_check_path": updated_service.health_check_path,
            "authentication_mode": updated_service.authentication_mode,
            "load_balancer_strategy": updated_service.load_balancer_strategy.value if hasattr(updated_service.load_balancer_strategy, "value") else updated_service.load_balancer_strategy,
            "status": updated_service.status
        })
        return updated_service

    @staticmethod
    async def delete_service(db: AsyncSession, service_id: int, project_id: int) -> Service:
        service = await ServiceService.get_service(db, service_id, project_id)
        service_cache.remove(service.service_name)
        return await service_repo.delete(db, id=service_id)
