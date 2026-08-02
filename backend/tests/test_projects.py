import pytest

@pytest.mark.asyncio
async def test_create_project(async_client, auth_headers):
    response = await async_client.post(
        "/api/v1/projects/",
        json={"name": "Test Project", "description": "A test project"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_projects(async_client, auth_headers):
    # First create a project
    await async_client.post(
        "/api/v1/projects/",
        json={"name": "Test Project 2"},
        headers=auth_headers
    )
    
    response = await async_client.get("/api/v1/projects/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_get_project(async_client, auth_headers):
    create_resp = await async_client.post(
        "/api/v1/projects/",
        json={"name": "Test Project 3"},
        headers=auth_headers
    )
    project_id = create_resp.json()["id"]

    response = await async_client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id

@pytest.mark.asyncio
async def test_update_project(async_client, auth_headers):
    create_resp = await async_client.post(
        "/api/v1/projects/",
        json={"name": "Test Project 4"},
        headers=auth_headers
    )
    project_id = create_resp.json()["id"]

    response = await async_client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Project 4", "description": "Updated desc"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project 4"

@pytest.mark.asyncio
async def test_delete_project(async_client, auth_headers):
    create_resp = await async_client.post(
        "/api/v1/projects/",
        json={"name": "Test Project 5"},
        headers=auth_headers
    )
    project_id = create_resp.json()["id"]

    response = await async_client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200

    get_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 404
