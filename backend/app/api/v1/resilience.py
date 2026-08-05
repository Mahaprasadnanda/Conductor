from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.connection import get_db_session
from app.schemas.resilience import ResiliencePolicyCreate, ResiliencePolicyUpdate, ResiliencePolicyResponse
from app.repositories.resilience import ResilienceRepository
from app.repositories.service import service_repo

router = APIRouter()
resilience_repo = ResilienceRepository()

@router.post("/", response_model=ResiliencePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_resilience_policy(
    policy_in: ResiliencePolicyCreate,
    db: AsyncSession = Depends(get_db_session)
):
    service = await service_repo.get(db, policy_in.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    existing = await resilience_repo.get_by_service_id(db, policy_in.service_id)
    if existing:
        raise HTTPException(status_code=400, detail="Resilience policy already exists for this service")
        
    return await resilience_repo.create(db, policy_in)

@router.get("/", response_model=List[ResiliencePolicyResponse])
async def list_resilience_policies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    return await resilience_repo.list_policies(db, skip=skip, limit=limit)

@router.get("/{policy_id}", response_model=ResiliencePolicyResponse)
async def get_resilience_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    policy = await resilience_repo.get_by_id(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Resilience policy not found")
    return policy

@router.put("/{policy_id}", response_model=ResiliencePolicyResponse)
async def update_resilience_policy(
    policy_id: int,
    policy_in: ResiliencePolicyUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    policy = await resilience_repo.get_by_id(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Resilience policy not found")
        
    return await resilience_repo.update(db, policy, policy_in)

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resilience_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    success = await resilience_repo.delete(db, policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resilience policy not found")
