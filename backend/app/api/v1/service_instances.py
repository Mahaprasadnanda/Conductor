from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.connection import get_db_session
from app.schemas.service_instance import ServiceInstanceCreate, ServiceInstanceUpdate, ServiceInstanceResponse
from app.repositories.service_instance import service_instance_repo
from app.repositories.service import service_repo

router = APIRouter()

@router.post("/", response_model=ServiceInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_service_instance(
    instance_in: ServiceInstanceCreate,
    db: AsyncSession = Depends(get_db_session)
):
    service = await service_repo.get(db, instance_in.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    existing = await service_instance_repo.get_by_instance_id(db, instance_in.instance_id)
    if existing:
        raise HTTPException(status_code=400, detail="Service instance already exists with this instance_id")
        
    return await service_instance_repo.create(db, instance_in)

@router.get("/service/{service_id}", response_model=List[ServiceInstanceResponse])
async def list_service_instances(
    service_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    service = await service_repo.get(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    return await service_instance_repo.get_by_service_id(db, service_id)

@router.get("/{instance_id}", response_model=ServiceInstanceResponse)
async def get_service_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    instance = await service_instance_repo.get(db, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Service instance not found")
    return instance

@router.put("/{instance_id}", response_model=ServiceInstanceResponse)
async def update_service_instance(
    instance_id: int,
    instance_in: ServiceInstanceUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    instance = await service_instance_repo.get(db, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Service instance not found")
        
    return await service_instance_repo.update(db, instance, instance_in)

@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    success = await service_instance_repo.delete(db, instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service instance not found")
