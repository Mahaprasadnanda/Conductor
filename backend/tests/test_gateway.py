import pytest
from httpx import AsyncClient, Response as HttpxResponse
from unittest.mock import patch

@pytest.mark.asyncio
async def test_proxy_gateway(async_client: AsyncClient, auth_headers: dict):
    # 1. Create a service first so it exists in cache
    # 2. But we don't really want to hit actual external service, we mock httpx
    
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    
    # Create service
    await async_client.post(
        "/api/v1/services/",
        json={
            "service_name": "test-backend",
            "base_url": "http://fake-backend:9000",
            "health_check_path": "/health"
        },
        headers=auth_headers
    )

    import httpx
    real_send = httpx.AsyncClient.send

    async def fake_send(self, request, *args, **kwargs):
        if "fake-backend" in str(request.url):
            return HttpxResponse(status_code=200, json={"message": "from proxy"}, request=request)
        return await real_send(self, request, *args, **kwargs)

    with patch("httpx.AsyncClient.send", new=fake_send):
        response = await async_client.get("/api/v1/gateway/test-backend/some/path?test=1", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json() == {"message": "from proxy"}
