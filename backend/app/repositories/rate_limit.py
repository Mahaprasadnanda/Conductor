from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.rate_limit import RateLimitPolicy
from app.schemas.rate_limit import RateLimitPolicyCreate, RateLimitPolicyUpdate

class RateLimitRepository:
    async def get(self, db: AsyncSession, id: int) -> Optional[RateLimitPolicy]:
        result = await db.execute(select(RateLimitPolicy).where(RateLimitPolicy.id == id))
        return result.scalars().first()

    async def get_all(self, db: AsyncSession) -> List[RateLimitPolicy]:
        result = await db.execute(select(RateLimitPolicy).order_by(RateLimitPolicy.id))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: RateLimitPolicyCreate) -> RateLimitPolicy:
        db_obj = RateLimitPolicy(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: RateLimitPolicy, obj_in: RateLimitPolicyUpdate) -> RateLimitPolicy:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

rate_limit_repo = RateLimitRepository()
