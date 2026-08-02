from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.repositories.base import BaseRepository
from app.models.endpoint import Endpoint
from app.schemas.endpoint import EndpointCreate, EndpointUpdate

class EndpointRepository(BaseRepository[Endpoint, EndpointCreate, EndpointUpdate]):
    async def get_multi_by_service(self, db: AsyncSession, service_id: int, skip: int = 0, limit: int = 100) -> list[Endpoint]:
        result = await db.execute(select(Endpoint).filter(Endpoint.service_id == service_id).offset(skip).limit(limit))
        return list(result.scalars().all())
        
    async def get_by_path_and_method(self, db: AsyncSession, service_id: int, path: str, method: str) -> Endpoint | None:
        result = await db.execute(select(Endpoint).filter(
            Endpoint.service_id == service_id,
            Endpoint.path == path,
            Endpoint.method == method
        ))
        return result.scalars().first()

    async def mark_inactive_for_service(self, db: AsyncSession, service_id: int) -> None:
        await db.execute(update(Endpoint).where(Endpoint.service_id == service_id).values(is_active=False))
        await db.commit()

endpoint_repo = EndpointRepository(Endpoint)
