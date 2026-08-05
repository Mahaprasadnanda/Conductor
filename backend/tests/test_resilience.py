import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import time

from app.main import app
from app.database.connection import get_redis, async_session_maker
from app.models.resilience import ResiliencePolicy
from app.models.service import Service, ServiceStatus

@pytest_asyncio.fixture(autouse=True)
async def setup_resilience(db_session, flush_redis):
    session = db_session
    # Create service
    service = Service(
        id=10,
        project_id=1,
        service_name="resilient_service",
        base_url="http://mock-upstream",
        status=ServiceStatus.HEALTHY,
        authentication_mode="DISABLED"
    )
    session.add(service)
    
    # Create resilience policy
    policy = ResiliencePolicy(
        service_id=10,
        failure_threshold=2,
        recovery_timeout=2,
        half_open_requests=1,
        retry_attempts=0,
        request_timeout=1,
        fallback_enabled=True,
        fallback_response={"message": "Fallback active"}
    )
    session.add(policy)
    await session.commit()
    
    # Patch async_session_maker to return our session
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_session_maker():
        yield session
        
    import app.gateway.middleware.resilience
    app.gateway.middleware.resilience.async_session_maker = mock_session_maker
    
    from app.gateway.cache import service_cache
    service_cache.set("resilient_service", {
        "id": 10,
        "project_id": 1,
        "service_name": "resilient_service",
        "base_url": "http://mock-upstream",
        "status": ServiceStatus.HEALTHY,
        "authentication_mode": "DISABLED"
    })

@pytest.mark.asyncio
async def test_resilience_circuit_breaker(flush_redis):
    # Mock proxy to fail 503
    from app.gateway.proxy.proxy import ProxyEngine
    from app.gateway.exceptions import ProxyException
    
    attempts = 0
    
    async def mock_forward_fail(context):
        nonlocal attempts
        attempts += 1
        raise ProxyException("Mocked 503")
        
    original_forward = ProxyEngine.forward
    ProxyEngine.forward = mock_forward_fail
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1st Request: will retry 2 times, total 3 attempts (1 initial + 2 retries)
            # Threshold is 2 failures!
            # 1st Request: records 1 failure, state remains CLOSED (threshold is 2).
            res = await client.get("/api/v1/gateway/resilient_service/test")
            assert res.status_code == 502 # ProxyException translates to 502 Bad Gateway
            assert "circuit_open" not in res.text
            
            # 2nd Request: records 2nd failure, state transitions to OPEN.
            res2 = await client.get("/api/v1/gateway/resilient_service/test")
            assert res2.status_code == 502
            
            # 3rd Request: Circuit is OPEN, should return Fallback!
            res3 = await client.get("/api/v1/gateway/resilient_service/test")
            assert res3.status_code == 503
            assert res3.json() == {"message": "Fallback active"}
            assert res3.headers["X-Circuit-State"] == "OPEN"
            
            # Wait for recovery timeout (3 seconds)
            time.sleep(3.0)
            
            # 4th Request: Should be HALF_OPEN
            # We mock a success this time to close the circuit
            async def mock_forward_success(context):
                from fastapi import Response
                return Response(content="success", status_code=200)
            
            ProxyEngine.forward = mock_forward_success
            
            res4 = await client.get("/api/v1/gateway/resilient_service/test")
            assert res4.status_code == 200
            # During request it was HALF_OPEN, after request it closed
            assert res4.text == "success"
            
    finally:
        ProxyEngine.forward = original_forward
