from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.project import ProjectService

router = APIRouter()

@router.get("/overview")
async def get_overview(
    project_id: int,
    time_range: str = "1h",
    service_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    return await AnalyticsService.get_overview(db, project_id, time_range, service_name)

@router.get("/timeseries")
async def get_timeseries(
    project_id: int,
    time_range: str = "1h", 
    service_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    return await AnalyticsService.get_timeseries(db, project_id, time_range=time_range, service_name=service_name)

@router.get("/recent-requests")
async def get_recent_requests(
    project_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    return await AnalyticsService.get_recent_requests(db, project_id, limit=limit)

@router.get("/recent-errors")
async def get_recent_errors(
    project_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    return await AnalyticsService.get_recent_errors(db, project_id, limit=limit)
