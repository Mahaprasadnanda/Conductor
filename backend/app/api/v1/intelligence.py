from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.intelligence import IntelligenceOverview
from app.services.traffic_intelligence import TrafficIntelligenceService
from app.services.project import ProjectService

router = APIRouter()

@router.get("/overview", response_model=IntelligenceOverview)
async def get_intelligence_overview(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get the current AI traffic intelligence overview including anomalies and recommendations."""
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    return await TrafficIntelligenceService.generate_overview(db, project_id)

@router.get("/anomalies")
async def get_anomalies(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get only the current anomalies."""
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    overview = await TrafficIntelligenceService.generate_overview(db, project_id)
    return {"anomalies": overview.recent_anomalies}

@router.get("/recommendations")
async def get_recommendations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get only the current recommendations."""
    await ProjectService.get_project(db, project_id, owner_id=current_user.id)
    overview = await TrafficIntelligenceService.generate_overview(db, project_id)
    return {"recommendations": overview.recommendations}
