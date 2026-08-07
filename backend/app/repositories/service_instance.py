from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.repositories.base import BaseRepository
from app.models.service import ServiceInstance
from app.schemas.service_instance import ServiceInstanceCreate, ServiceInstanceUpdate

class ServiceInstanceRepository(BaseRepository[ServiceInstance, ServiceInstanceCreate, ServiceInstanceUpdate]):
    async def get_by_instance_id(self, db: AsyncSession, instance_id: str) -> ServiceInstance | None:
        result = await db.execute(select(ServiceInstance).filter(ServiceInstance.instance_id == instance_id))
        return result.scalars().first()

    async def get_by_service_id(self, db: AsyncSession, service_id: int) -> list[ServiceInstance]:
        result = await db.execute(select(ServiceInstance).filter(ServiceInstance.service_id == service_id))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: ServiceInstanceCreate) -> ServiceInstance:
        import uuid
        obj_in_data = obj_in.model_dump()
        if not obj_in_data.get("instance_id"):
            obj_in_data["instance_id"] = str(uuid.uuid4())
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

service_instance_repo = ServiceInstanceRepository(ServiceInstance)
