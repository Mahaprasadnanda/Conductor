from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    async def get_multi_by_owner(self, db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> list[Project]:
        result = await db.execute(select(Project).filter(Project.owner_id == owner_id).offset(skip).limit(limit))
        return list(result.scalars().all())

project_repo = ProjectRepository(Project)
