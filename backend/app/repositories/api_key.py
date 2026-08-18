from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate

class ApiKeyRepository(BaseRepository[ApiKey, ApiKeyCreate, ApiKeyCreate]):
    
    async def get_by_hash(self, db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
        result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True))
        return result.scalars().first()

    async def get_multi_by_project(self, db: AsyncSession, project_id: int) -> List[ApiKey]:
        result = await db.execute(
            select(ApiKey).where(ApiKey.project_id == project_id).order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

api_key_repo = ApiKeyRepository(ApiKey)
