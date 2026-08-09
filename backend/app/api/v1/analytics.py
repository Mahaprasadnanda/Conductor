from fastapi import APIRouter, Depends
from typing import Optional
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/overview")
async def get_overview(current_user: User = Depends(get_current_user)):
    return await AnalyticsService.get_overview()

@router.get("/timeseries")
async def get_timeseries(
    time_range: str = "1h", 
    service_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    return await AnalyticsService.get_timeseries(time_range=time_range, service_name=service_name)

@router.get("/recent-requests")
async def get_recent_requests(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    return await AnalyticsService.get_recent_requests(limit=limit)

@router.get("/recent-errors")
async def get_recent_errors(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    return await AnalyticsService.get_recent_errors(limit=limit)
