from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyReveal
from app.services.api_key_service import ApiKeyService

router = APIRouter()

@router.post("/", response_model=ApiKeyReveal, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_in: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await ApiKeyService.create_api_key(db, current_user.id, key_in)

@router.get("/", response_model=List[ApiKeyResponse])
async def list_api_keys(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await ApiKeyService.list_api_keys(db, current_user.id, project_id)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await ApiKeyService.revoke_api_key(db, current_user.id, key_id)
