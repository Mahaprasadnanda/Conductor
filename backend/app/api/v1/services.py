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
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
    
    return await ServiceService.create_service(db, service_in, project_id=project_id)

@router.get("/", response_model=list[ServiceResponse])
async def list_services(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
        
    return await ServiceService.list_services(db, project_id=project_id, skip=skip, limit=limit)

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
        
    service = await ServiceService.get_service(db, service_id, project_id)
    if service_in.service_name and service_in.service_name != service.service_name:
        raise HTTPException(status_code=400, detail="Service name is immutable to protect routing consistency")
        
    return await ServiceService.update_service(db, service_id, service_in, project_id)

@router.post("/{service_id}/import", response_model=list[EndpointResponse])
async def import_openapi(
    service_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
        
    service = await ServiceService.get_service(db, service_id, project_id)
    if not service.openapi_url:
        raise HTTPException(status_code=400, detail="Service has no openapi_url defined.")

    service_update = ServiceUpdate(status=ServiceStatus.IMPORTING)
    await ServiceService.update_service(db, service_id, service_update, project_id)

    endpoints_in = await OpenAPIImporter.fetch_and_parse(service.openapi_url)
    
    synced = await EndpointService.sync_endpoints(db, service_id, endpoints_in)
    
    service_update = ServiceUpdate(status=ServiceStatus.UNKNOWN)
    await ServiceService.update_service(db, service_id, service_update, project_id)
    
    return synced

@router.get("/{service_id}/endpoints", response_model=list[EndpointResponse])
async def list_endpoints(
    service_id: int,
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
        
    await ServiceService.get_service(db, service_id, project_id)
    
    return await EndpointService.list_endpoints(db, service_id, skip=skip, limit=limit)

@router.delete("/{service_id}", response_model=ServiceResponse)
async def delete_service(
    service_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from app.repositories.project import project_repo
    project = await project_repo.get(db, id=project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")
        
    return await ServiceService.delete_service(db, service_id, project_id)
