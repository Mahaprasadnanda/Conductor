import pytest
from httpx import AsyncClient, Response as HttpxResponse
from unittest.mock import patch

@pytest.mark.asyncio
async def test_proxy_gateway_with_api_key(async_client: AsyncClient, auth_headers: dict):
    # 1. Create a project
    proj_res = await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]
    
    # 2. Create service
    await async_client.post(
        f"/api/v1/services/?project_id={project_id}",
        json={
            "service_name": "test-backend",
            "base_url": "http://fake-backend:9000",
            "health_check_path": "/health",
            "authentication_mode": "API_KEY_REQUIRED"
        },
        headers=auth_headers
    )

    # 3. Create API key
    key_res = await async_client.post(
        "/api/v1/api_keys/",
        json={"name": "Test Key", "project_id": project_id},
        headers=auth_headers
    )
    assert key_res.status_code == 201
    raw_key = key_res.json()["raw_key"]

    import httpx
    real_send = httpx.AsyncClient.send

    async def fake_send(self, request, *args, **kwargs):
        if "fake-backend" in str(request.url) or "host.docker.internal" in str(request.url):
            return HttpxResponse(status_code=200, json={"message": "from proxy"}, request=request)
        return await real_send(self, request, *args, **kwargs)

    # 4. Access gateway with API key and Host header
    with patch("httpx.AsyncClient.send", new=fake_send):
        response = await async_client.get(
            "/some/path",
            headers={"Authorization": f"Bearer {raw_key}", "Host": "test-backend.api.localhost:8000"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "from proxy"}

@pytest.mark.asyncio
async def test_proxy_gateway_rejects_jwt(async_client: AsyncClient, auth_headers: dict):
    # 1. Create a project
    proj_res = await async_client.post("/api/v1/projects/", json={"name": "Test P2"}, headers=auth_headers)
    project_id = proj_res.json()["id"]
    
    # 2. Create service with API_KEY_REQUIRED
    await async_client.post(
        f"/api/v1/services/?project_id={project_id}",
        json={
            "service_name": "test-backend2",
            "base_url": "http://fake-backend:9000",
            "health_check_path": "/health",
            "authentication_mode": "API_KEY_REQUIRED"
        },
        headers=auth_headers
    )

    # Try accessing with JWT
    response = await async_client.get(
        "/some/path",
        headers={"Authorization": auth_headers["Authorization"], "Host": "test-backend2.api.localhost:8000"}
    )
    # Since it's a proxy route, it expects an API key, so JWT validation will fail
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or revoked API key"
