from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.endpoint import endpoint_repo
from app.schemas.endpoint import EndpointCreate, EndpointUpdate
from app.models.endpoint import Endpoint

class EndpointService:
    @staticmethod
    async def sync_endpoints(db: AsyncSession, service_id: int, discovered_endpoints: list[EndpointCreate]) -> list[Endpoint]:
        # Soft delete existing endpoints
        await endpoint_repo.mark_inactive_for_service(db, service_id)
        
        synced = []
        for ep_in in discovered_endpoints:
            existing = await endpoint_repo.get_by_path_and_method(db, service_id=service_id, path=ep_in.path, method=ep_in.method)
            if existing:
                ep_data = ep_in.model_dump()
                ep_data.pop("is_active", None)
                ep_update = EndpointUpdate(**ep_data, is_active=True)
                updated = await endpoint_repo.update(db, db_obj=existing, obj_in=ep_update)
                synced.append(updated)
            else:
                ep_data = ep_in.model_dump()
                ep_data.pop("is_active", None)
                db_ep = Endpoint(**ep_data, service_id=service_id, is_active=True)
                db.add(db_ep)
                synced.append(db_ep)
                
        await db.commit()
        return synced

    @staticmethod
    async def list_endpoints(db: AsyncSession, service_id: int, skip: int = 0, limit: int = 100) -> list[Endpoint]:
        return await endpoint_repo.get_multi_by_service(db, service_id=service_id, skip=skip, limit=limit)
