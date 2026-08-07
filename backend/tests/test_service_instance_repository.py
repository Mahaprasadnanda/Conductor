import pytest
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.service_instance import service_instance_repo
from app.schemas.service_instance import ServiceInstanceCreate
from app.models.service import Service, ServiceStatus
from app.repositories.service import service_repo

@pytest.mark.asyncio
async def test_service_instance_creation(db_session: AsyncSession, test_user):
    from app.models.project import Project
    # Setup project
    project = Project(
        id=1,
        name="test_project_for_instances",
        owner_id=test_user.id
    )
    db_session.add(project)
    
    # Setup parent service
    service = Service(
        project_id=1,
        service_name="test_service_for_instances",
        base_url="http://test-service",
        health_check_path="/health"
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)

    # 1. Create without instance_id
    instance_in_1 = ServiceInstanceCreate(
        service_id=service.id,
        base_url="http://node1"
    )
    db_obj_1 = await service_instance_repo.create(db_session, instance_in_1)
    
    assert db_obj_1.id is not None
    assert db_obj_1.instance_id is not None
    assert isinstance(db_obj_1.instance_id, str)
    assert len(db_obj_1.instance_id) > 0

    # 2. Create with explicit instance_id
    custom_id = "custom-instance-123"
    instance_in_2 = ServiceInstanceCreate(
        service_id=service.id,
        base_url="http://node2",
        instance_id=custom_id
    )
    db_obj_2 = await service_instance_repo.create(db_session, instance_in_2)
    
    assert db_obj_2.id is not None
    assert db_obj_2.instance_id == custom_id

    # 3. Uniqueness of generated UUID (creating another one without instance_id)
    instance_in_3 = ServiceInstanceCreate(
        service_id=service.id,
        base_url="http://node3"
    )
    db_obj_3 = await service_instance_repo.create(db_session, instance_in_3)
    
    assert db_obj_3.instance_id is not None
    assert db_obj_1.instance_id != db_obj_3.instance_id

    # 4. Successful persistence
    fetched = await service_instance_repo.get_by_instance_id(db_session, db_obj_1.instance_id)
    assert fetched is not None
    assert fetched.id == db_obj_1.id
