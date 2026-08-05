import pytest
import asyncio
from httpx import AsyncClient
from fastapi.responses import Response
from app.gateway.cache import service_cache
from app.models.service import ServiceStatus, ServiceAuthMode
from unittest.mock import patch

async def mock_forward(*args, **kwargs):
    return Response(content=b"OK", status_code=200)

@pytest.fixture(autouse=True)
def setup_services():
    service_cache.set("test-service", {
        "id": 1,
        "service_name": "test-service",
        "base_url": "http://upstream",
        "authentication_mode": ServiceAuthMode.PUBLIC,
        "status": ServiceStatus.HEALTHY
    })
    service_cache.set("test-service-2", {
        "id": 2,
        "service_name": "test-service-2",
        "base_url": "http://upstream2",
        "authentication_mode": ServiceAuthMode.PUBLIC,
        "status": ServiceStatus.HEALTHY
    })
    
    async def mock_get_policy(self, service_id, endpoint):
        return {"id": 1, "limit": 100, "window": 60, "algo": "SLIDING_WINDOW_LOG"}
        
    policy_patcher = patch("app.gateway.middleware.rate_limiter.RateLimiterMiddleware._get_policy", new=mock_get_policy)
    policy_patcher.start()
    
    from redis.asyncio import Redis
    from app.config.settings import settings
    
    def mock_get_redis():
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)
        
    redis_patcher = patch("app.gateway.middleware.rate_limiter.get_redis", side_effect=mock_get_redis)
    redis_patcher.start()
    
    from app.gateway.middleware.registry import RateLimiterMiddleware
    # The pipeline instantiates middlewares, wait, if pipeline is a singleton, the middleware instance persists.
    # Let's just patch the pipeline or clear it directly if accessible.
    # Actually, just reset it in the SlidingWindowLogStrategy class!
    # No, it's an instance variable on RateLimiterMiddleware.strategy.
    # It's better to just pass the script inline, or clear it. Let's patch register_script.
    
    yield
    
    policy_patcher.stop()
    redis_patcher.stop()
    service_cache.remove("test-service")
    service_cache.remove("test-service-2")

@pytest.mark.asyncio
async def test_request_under_limit(async_client: AsyncClient):
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        response = await async_client.get("/api/v1/gateway/test-service/path")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
        assert int(response.headers["X-RateLimit-Remaining"]) == 99

@pytest.mark.asyncio
async def test_request_exceeding_limit(async_client: AsyncClient):
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        for _ in range(100):
            res = await async_client.get("/api/v1/gateway/test-service/path")
            assert res.status_code == 200
            
        response = await async_client.get("/api/v1/gateway/test-service/path")
        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limit exceeded"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in response.headers

@pytest.mark.asyncio
async def test_reset_after_window(async_client: AsyncClient):
    import time
    original_time = time.time
    mock_time = original_time()
    
    def fake_time():
        return mock_time
        
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        with patch("app.gateway.middleware.rate_limiter.time.time", side_effect=fake_time):
            for _ in range(100):
                await async_client.get("/api/v1/gateway/test-service/path")
                
            res = await async_client.get("/api/v1/gateway/test-service/path")
            assert res.status_code == 429
            
            mock_time += 61
            
            res = await async_client.get("/api/v1/gateway/test-service/path")
            assert res.status_code == 200
            assert int(res.headers["X-RateLimit-Remaining"]) == 99

@pytest.mark.asyncio
async def test_different_users_independent_limits(async_client: AsyncClient, auth_headers):
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        service_cache.set("test-service", {
            "id": 1,
            "service_name": "test-service",
            "base_url": "http://upstream",
            "authentication_mode": ServiceAuthMode.JWT_REQUIRED,
            "status": ServiceStatus.HEALTHY
        })
        
        for _ in range(100):
            await async_client.get("/api/v1/gateway/test-service/path", headers=auth_headers)
            
        res1 = await async_client.get("/api/v1/gateway/test-service/path", headers=auth_headers)
        assert res1.status_code == 429

@pytest.mark.asyncio
async def test_different_services_independent_limits(async_client: AsyncClient):
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        for _ in range(100):
            await async_client.get("/api/v1/gateway/test-service/path")
            
        res1 = await async_client.get("/api/v1/gateway/test-service/path")
        assert res1.status_code == 429
        
        res2 = await async_client.get("/api/v1/gateway/test-service-2/path")
        assert res2.status_code == 200
        assert int(res2.headers["X-RateLimit-Remaining"]) == 99

@pytest.mark.asyncio
async def test_redis_unavailable_fail_open(async_client: AsyncClient):
    from redis.exceptions import ConnectionError
    with patch("app.gateway.proxy.proxy.ProxyEngine.forward", new=mock_forward):
        with patch("redis.asyncio.Redis.register_script", side_effect=ConnectionError("Redis down")):
            res = await async_client.get("/api/v1/gateway/test-service/path")
            assert res.status_code == 200
            assert "X-RateLimit-Remaining" in res.headers
