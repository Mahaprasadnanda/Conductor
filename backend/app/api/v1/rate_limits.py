from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.connection import get_db_session
from app.schemas.rate_limit import RateLimitPolicyCreate, RateLimitPolicyUpdate, RateLimitPolicyResponse
from app.repositories.rate_limit import rate_limit_repo
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=RateLimitPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_limit(policy_in: RateLimitPolicyCreate, db: AsyncSession = Depends(get_db_session), current_user = Depends(get_current_user)):
    return await rate_limit_repo.create(db, policy_in)

@router.get("/", response_model=List[RateLimitPolicyResponse])
async def list_rate_limits(db: AsyncSession = Depends(get_db_session), current_user = Depends(get_current_user)):
    return await rate_limit_repo.get_all(db)

@router.get("/{id}", response_model=RateLimitPolicyResponse)
async def get_rate_limit(id: int, db: AsyncSession = Depends(get_db_session), current_user = Depends(get_current_user)):
    policy = await rate_limit_repo.get(db, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
    return policy

@router.put("/{id}", response_model=RateLimitPolicyResponse)
async def update_rate_limit(id: int, policy_in: RateLimitPolicyUpdate, db: AsyncSession = Depends(get_db_session), current_user = Depends(get_current_user)):
    policy = await rate_limit_repo.get(db, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
    return await rate_limit_repo.update(db, policy, policy_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_limit(id: int, db: AsyncSession = Depends(get_db_session), current_user = Depends(get_current_user)):
    success = await rate_limit_repo.delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
