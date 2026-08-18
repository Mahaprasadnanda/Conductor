import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.schemas.endpoint import EndpointCreate
from app.models.service import ServiceStatus

@pytest.fixture
def mock_openapi_spec():
    return [
        EndpointCreate(
            path="/users",
            method="GET",
            operation_id="get_users",
            summary="Get Users",
            tags=["Users"]
        ),
        EndpointCreate(
            path="/users",
            method="POST",
            operation_id="create_user",
            summary="Create User",
            tags=["Users"]
        )
    ]

@pytest.mark.asyncio
async def test_create_service(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    # Test Create
    response = await async_client.post(
        "/api/v1/services/?project_id=1",
        json={
            "service_name": "user-service",
            "base_url": "http://user-service:8080",
            "openapi_url": "http://user-service:8080/openapi.json",
            "health_check_path": "/healthz"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["service_name"] == "user-service"
    assert data["status"] == ServiceStatus.UNKNOWN.value

@pytest.mark.asyncio
async def test_list_services(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    await async_client.post("/api/v1/services/?project_id=1", json={"service_name": "list-service", "base_url": "http://list-service"}, headers=auth_headers)
    
    response = await async_client.get("/api/v1/services/?project_id=1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_import_openapi(async_client: AsyncClient, auth_headers: dict, mock_openapi_spec):
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    await async_client.post("/api/v1/services/?project_id=1", json={"service_name": "import-service", "base_url": "http://import-service", "openapi_url": "http://test.com/openapi.json"}, headers=auth_headers)
    
    # Get service ID
    res = await async_client.get("/api/v1/services/?project_id=1", headers=auth_headers)
    service_id = res.json()[0]["id"]

    with patch("app.gateway.importer.OpenAPIImporter.fetch_and_parse", return_value=mock_openapi_spec):
        response = await async_client.post(f"/api/v1/services/{service_id}/import?project_id=1", headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["path"] == "/users"

@pytest.mark.asyncio
async def test_list_endpoints(async_client: AsyncClient, auth_headers: dict, mock_openapi_spec):
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    await async_client.post("/api/v1/services/?project_id=1", json={"service_name": "ep-service", "base_url": "http://ep-service", "openapi_url": "http://test.com/openapi.json"}, headers=auth_headers)
    
    res = await async_client.get("/api/v1/services/?project_id=1", headers=auth_headers)
    service_id = res.json()[0]["id"]

    with patch("app.gateway.importer.OpenAPIImporter.fetch_and_parse", return_value=mock_openapi_spec):
        await async_client.post(f"/api/v1/services/{service_id}/import?project_id=1", headers=auth_headers)

    response = await async_client.get(f"/api/v1/services/{service_id}/endpoints?project_id=1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_update_service(async_client: AsyncClient, auth_headers: dict):
    # Setup
    await async_client.post("/api/v1/projects/", json={"name": "Test P Update"}, headers=auth_headers)
    res = await async_client.post(
        "/api/v1/services/?project_id=1",
        json={"service_name": "update-service", "base_url": "http://update-service"},
        headers=auth_headers
    )
    service_id = res.json()["id"]

    # Test update valid fields
    update_res = await async_client.put(
        f"/api/v1/services/{service_id}?project_id=1",
        json={"base_url": "http://new-url", "health_check_path": "/new-health"},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["base_url"] == "http://new-url" # HttpUrl adds trailing slash in schema but service_service removes it for db, wait HttpUrl representation might differ
    assert updated_data["health_check_path"] == "/new-health"
    
    # Test update immutable service name
    update_name_res = await async_client.put(
        f"/api/v1/services/{service_id}?project_id=1",
        json={"service_name": "changed-name"},
        headers=auth_headers
    )
    assert update_name_res.status_code == 400

    # Test Disable
    disable_res = await async_client.put(
        f"/api/v1/services/{service_id}?project_id=1",
        json={"status": "Disabled"},
        headers=auth_headers
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["status"] == "Disabled"
