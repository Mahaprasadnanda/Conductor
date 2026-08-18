import secrets
import hashlib
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyReveal, ApiKeyResponse
from app.repositories.api_key import api_key_repo
from app.repositories.project import project_repo

class ApiKeyService:
    PREFIX = "cond_live_"

    @staticmethod
    def _generate_key() -> Tuple[str, str]:
        """Generates a raw key and its SHA-256 hash."""
        random_part = secrets.token_urlsafe(32)
        raw_key = f"{ApiKeyService.PREFIX}{random_part}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return raw_key, key_hash

    @staticmethod
    async def create_api_key(db: AsyncSession, user_id: int, key_in: ApiKeyCreate) -> ApiKeyReveal:
        # Verify user owns project
        project = await project_repo.get(db, id=key_in.project_id)
        if not project or project.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this project")

        raw_key, key_hash = ApiKeyService._generate_key()
        
        # We store just enough prefix to help user identify the key later, e.g. cond_live_xxxx
        prefix_display = raw_key[:14] 

        db_obj = ApiKey(
            project_id=key_in.project_id,
            name=key_in.name,
            key_hash=key_hash,
            prefix=prefix_display,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        return ApiKeyReveal(
            id=db_obj.id,
            project_id=db_obj.project_id,
            name=db_obj.name,
            prefix=db_obj.prefix,
            is_active=db_obj.is_active,
            created_at=db_obj.created_at,
            last_used_at=db_obj.last_used_at,
            raw_key=raw_key
        )

    @staticmethod
    async def list_api_keys(db: AsyncSession, user_id: int, project_id: int) -> List[ApiKeyResponse]:
        project = await project_repo.get(db, id=project_id)
        if not project or project.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this project")
            
        return await api_key_repo.get_multi_by_project(db, project_id)

    @staticmethod
    async def revoke_api_key(db: AsyncSession, user_id: int, key_id: int) -> None:
        key = await api_key_repo.get(db, id=key_id)
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")
            
        project = await project_repo.get(db, id=key.project_id)
        if not project or project.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this project")

        key.is_active = False
        await db.commit()
