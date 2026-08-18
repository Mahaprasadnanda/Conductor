import pytest
from httpx import AsyncClient, Response as HttpxResponse, Request as HttpxRequest
from unittest.mock import patch, MagicMock, AsyncMock
from app.gateway.context import RequestContext
from app.gateway.pipeline import GatewayPipeline
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.middleware.registry import register_middleware, _registry
from app.gateway.proxy.proxy import ProxyEngine
from fastapi import Request

# Dummy middleware to track execution order
execution_log = []

class TrackingMiddleware(BaseMiddleware):
    def __init__(self, name):
        self.name = name

    async def before_request(self, context: RequestContext) -> None:
        execution_log.append(f"{self.name}_before")

    async def after_response(self, context: RequestContext, response) -> None:
        execution_log.append(f"{self.name}_after")

@pytest.fixture(autouse=True)
def reset_execution_log():
    execution_log.clear()

@pytest.mark.asyncio
async def test_middleware_execution_order():
    # Register trackers
    class TrackID(TrackingMiddleware):
        def __init__(self): super().__init__("request_id")
    class TrackAuth(TrackingMiddleware):
        def __init__(self): super().__init__("auth")
    class TrackTiming(TrackingMiddleware):
        def __init__(self): super().__init__("timing")
    class TrackLogging(TrackingMiddleware):
        def __init__(self): super().__init__("logging")
        
    register_middleware("track_id", TrackID)
    register_middleware("track_auth", TrackAuth)
    register_middleware("track_timing", TrackTiming)
    register_middleware("track_logging", TrackLogging)
    
    pipeline = GatewayPipeline(["track_id", "track_auth", "track_timing", "track_logging"])
    
    context = RequestContext.create()
    
    async def mock_proxy(ctx):
        execution_log.append("proxy")
        return "response"
        
    await pipeline.execute(context, mock_proxy)
    
    assert execution_log == [
        "request_id_before",
        "auth_before",
        "timing_before",
        "logging_before",
        "proxy",
        "logging_after",
        "timing_after",
        "auth_after",
        "request_id_after"
    ]

@pytest.mark.asyncio
async def test_after_response_executes_on_proxy_failure():
    class TrackAuth(TrackingMiddleware):
        def __init__(self): super().__init__("auth")
        
    register_middleware("track_auth", TrackAuth)
    pipeline = GatewayPipeline(["track_auth"])
    context = RequestContext.create()
    
    async def mock_proxy_fail(ctx):
        execution_log.append("proxy_fail")
        raise Exception("Proxy failed")
        
    with pytest.raises(Exception):
        await pipeline.execute(context, mock_proxy_fail)
        
    assert execution_log == [
        "auth_before",
        "proxy_fail",
        "auth_after"
    ]

@pytest.mark.asyncio
async def test_gateway_route_integration(async_client: AsyncClient, auth_headers: dict):
    # Create project and service
    await async_client.post("/api/v1/projects/", json={"name": "Test P"}, headers=auth_headers)
    await async_client.post(
        "/api/v1/services/?project_id=1",
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
            return HttpxResponse(200, json={"message": "from proxy"}, request=request)
        return await real_send(self, request, *args, **kwargs)

    with patch("httpx.AsyncClient.send", new=fake_send):
        res = await async_client.get("/api/v1/gateway/test-backend/path", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == {"message": "from proxy"}
        
        # Test missing auth if mode is JWT_REQUIRED
        res_no_auth = await async_client.get("/api/v1/gateway/test-backend/path")
        assert res_no_auth.status_code == 401

@pytest.mark.asyncio
async def test_host_routing_prevents_double_prefix(async_client: AsyncClient, auth_headers: dict):
    # This test verifies that if the client specifies the fully qualified gateway path 
    # while hitting the host-routed subdomain, the path doesn't get double prefixed.
    # Note: async_client hits host "testclient" by default, we need to override host header.
    
    # Ensure project and service exist (state might carry over, but let's be safe if they do)
    try:
        await async_client.post("/api/v1/projects/", json={"name": "Test P2"}, headers=auth_headers)
    except:
        pass
        
    try:
        await async_client.post(
            "/api/v1/services/?project_id=1",
            json={
                "service_name": "demoo",
                "base_url": "http://fake-backend2:9000",
                "health_check_path": "/health"
            },
            headers=auth_headers
        )
    except:
        pass

    import httpx
    real_send = httpx.AsyncClient.send
    
    captured_url = None

    async def fake_send(self, request, *args, **kwargs):
        nonlocal captured_url
        captured_url = str(request.url)
        if "fake-backend" in str(request.url):
            return HttpxResponse(200, json={"message": "from proxy"}, request=request)
        return await real_send(self, request, *args, **kwargs)

    with patch("httpx.AsyncClient.send", new=fake_send):
        res = await async_client.get(
            "/api/v1/gateway/demoo/health", 
            headers={**auth_headers, "host": "demoo.api.localhost:8000"}
        )
        assert res.status_code == 200
        assert res.json() == {"message": "from proxy"}
        assert captured_url == "http://fake-backend2:9000/health"

