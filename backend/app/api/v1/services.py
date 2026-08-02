from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from app.schemas.endpoint import EndpointResponse
from app.services.service_service import ServiceService
from app.services.endpoint_service import EndpointService
from app.gateway.importer import OpenAPIImporter
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.service import ServiceStatus

router = APIRouter()

@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    current_user: User = Depends(get_current_user),
    # For now, require a project_id. Wait, our schema doesn't have project_id, let's just pass a default project or expect it in query since it's v1.
    # To keep it simple, we fetch user's first project.
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    projects = await project_repo.get_multi_by_owner(db, current_user.id)
    if not projects:
        raise HTTPException(status_code=400, detail="User has no projects to attach service to.")
    
    return await ServiceService.create_service(db, service_in, project_id=projects[0].id)

@router.get("/", response_model=list[ServiceResponse])
async def list_services(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    projects = await project_repo.get_multi_by_owner(db, current_user.id)
    if not projects:
        return []
        
    # Simplify by returning services for the first project
    return await ServiceService.list_services(db, project_id=projects[0].id, skip=skip, limit=limit)

@router.post("/{service_id}/import", response_model=list[EndpointResponse])
async def import_openapi(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    projects = await project_repo.get_multi_by_owner(db, current_user.id)
    if not projects:
        raise HTTPException(status_code=400, detail="User has no projects.")
        
    service = await ServiceService.get_service(db, service_id, projects[0].id)
    if not service.openapi_url:
        raise HTTPException(status_code=400, detail="Service has no openapi_url defined.")

    # Mark as importing
    service_update = ServiceUpdate(status=ServiceStatus.IMPORTING)
    await ServiceService.update_service(db, service_id, service_update, projects[0].id)

    # Fetch and parse
    endpoints_in = await OpenAPIImporter.fetch_and_parse(service.openapi_url)
    
    # Sync endpoints
    synced = await EndpointService.sync_endpoints(db, service_id, endpoints_in)
    
    # Reset status
    service_update = ServiceUpdate(status=ServiceStatus.UNKNOWN)
    await ServiceService.update_service(db, service_id, service_update, projects[0].id)
    
    return synced

@router.get("/{service_id}/endpoints", response_model=list[EndpointResponse])
async def list_endpoints(
    service_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    projects = await project_repo.get_multi_by_owner(db, current_user.id)
    if not projects:
        raise HTTPException(status_code=400, detail="User has no projects.")
        
    # Verify service ownership
    await ServiceService.get_service(db, service_id, projects[0].id)
    
    return await EndpointService.list_endpoints(db, service_id, skip=skip, limit=limit)
