import pytest
from httpx import AsyncClient
from app.models.api_key import ApiKey
from app.repositories.api_key import api_key_repo
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_api_key(async_client: AsyncClient, auth_headers: dict, db_session):
    # Get a project or create one
    response = await async_client.get("/api/v1/projects/", headers=auth_headers)
    projects = response.json()
    if not projects:
        res = await async_client.post("/api/v1/projects/", headers=auth_headers, json={"name": "Test Project"})
        projects = [res.json()]
    
    project_id = projects[0]["id"]
    
    # Create key
    response = await async_client.post(
        "/api/v1/api_keys/",
        headers=auth_headers,
        json={"name": "Test Key", "project_id": project_id}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Key"
    assert "raw_key" in data
    assert data["raw_key"].startswith("cond_live_")
    assert data["is_active"] is True
    
    # List keys
    response = await async_client.get(
        f"/api/v1/api_keys/?project_id={project_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) >= 1
    assert keys[0]["name"] == "Test Key"
    assert "raw_key" not in keys[0]

@pytest.mark.asyncio
async def test_revoke_api_key(async_client: AsyncClient, auth_headers: dict, db_session):
    # Get a project
    response = await async_client.get("/api/v1/projects/", headers=auth_headers)
    projects = response.json()
    if not projects:
        res = await async_client.post("/api/v1/projects/", headers=auth_headers, json={"name": "Test Project"})
        projects = [res.json()]
    
    project_id = projects[0]["id"]
    
    # Create key
    response = await async_client.post(
        "/api/v1/api_keys/",
        headers=auth_headers,
        json={"name": "Revoke Me", "project_id": project_id}
    )
    
    assert response.status_code == 201
    data = response.json()
    key_id = data["id"]
    
    # Revoke key
    response = await async_client.delete(
        f"/api/v1/api_keys/{key_id}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Verify in DB
    key = await api_key_repo.get(db_session, id=key_id)
    assert key.is_active is False
