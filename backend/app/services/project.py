from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.project import project_repo
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.project import Project

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, project_in: ProjectCreate, owner_id: int) -> Project:
        db_project = Project(**project_in.model_dump(), owner_id=owner_id)
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        return db_project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int, owner_id: int) -> Project:
        project = await project_repo.get(db, id=project_id)
        if not project or project.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    @staticmethod
    async def list_projects(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> list[Project]:
        return await project_repo.get_multi_by_owner(db, owner_id=owner_id, skip=skip, limit=limit)

    @staticmethod
    async def update_project(db: AsyncSession, project_id: int, project_in: ProjectUpdate, owner_id: int) -> Project:
        project = await ProjectService.get_project(db, project_id, owner_id)
        return await project_repo.update(db, db_obj=project, obj_in=project_in)

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: int, owner_id: int) -> Project:
        project = await ProjectService.get_project(db, project_id, owner_id)
        return await project_repo.delete(db, id=project_id)
