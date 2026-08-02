from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class ServiceRepository(BaseRepository[Service, ServiceCreate, ServiceUpdate]):
    async def get_by_name(self, db: AsyncSession, service_name: str) -> Service | None:
        result = await db.execute(select(Service).filter(Service.service_name == service_name))
        return result.scalars().first()
        
    async def get_multi_by_project(self, db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> list[Service]:
        result = await db.execute(select(Service).filter(Service.project_id == project_id).offset(skip).limit(limit))
        return list(result.scalars().all())

service_repo = ServiceRepository(Service)
