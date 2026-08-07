import pytest
import httpx
import asyncio
from app.gateway.registry import ServiceRegistry
from app.models.service import ServiceStatus

@pytest.mark.asyncio
async def test_health_check_normal():
    # Setup mock response
    class MockResponse:
        status_code = 200
        async def aread(self): pass
        def json(self): return {"status": "healthy"}
        
    class MockStream:
        async def __aenter__(self): return MockResponse()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def stream(self, method, url, **kwargs): return MockStream()
        
    import httpx
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: MockClient()
    
    try:
        service_data = {"service_name": "test", "base_url": "http://localhost", "health_check_path": "/health"}
        name, status = await ServiceRegistry.check_health(service_data)
        assert status == ServiceStatus.HEALTHY
    finally:
        httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_health_check_malformed_json():
    class MockResponse:
        status_code = 200
        async def aread(self): pass
        def json(self): raise ValueError("malformed json")
        
    class MockStream:
        async def __aenter__(self): return MockResponse()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def stream(self, method, url, **kwargs): return MockStream()
        
    import httpx
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: MockClient()
    
    try:
        service_data = {"service_name": "test", "base_url": "http://localhost", "health_check_path": "/health"}
        name, status = await ServiceRegistry.check_health(service_data)
        assert status == ServiceStatus.HEALTHY
    finally:
        httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_health_check_explicit_unhealthy():
    class MockResponse:
        status_code = 200
        async def aread(self): pass
        def json(self): return {"status": "unhealthy"}
        
    class MockStream:
        async def __aenter__(self): return MockResponse()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def stream(self, method, url, **kwargs): return MockStream()
        
    import httpx
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: MockClient()
    
    try:
        service_data = {"service_name": "test", "base_url": "http://localhost", "health_check_path": "/health"}
        name, status = await ServiceRegistry.check_health(service_data)
        assert status == ServiceStatus.UNHEALTHY
    finally:
        httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_health_check_delayed_body():
    class MockResponse:
        status_code = 200
        async def aread(self): 
            raise httpx.ReadTimeout("Timeout reading body")
        def json(self): raise httpx.ReadTimeout("Timeout")
        
    class MockStream:
        async def __aenter__(self): return MockResponse()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def stream(self, method, url, **kwargs): return MockStream()
        
    import httpx
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: MockClient()
    
    try:
        service_data = {"service_name": "test", "base_url": "http://localhost", "health_check_path": "/health"}
        name, status = await ServiceRegistry.check_health(service_data)
        assert status == ServiceStatus.HEALTHY
    finally:
        httpx.AsyncClient = original_client

@pytest.mark.asyncio
async def test_health_check_connection_timeout():
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        def stream(self, method, url, **kwargs): 
            raise httpx.ConnectTimeout("Connect timeout")
            
    import httpx
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: MockClient()
    
    try:
        service_data = {"service_name": "test", "base_url": "http://localhost", "health_check_path": "/health"}
        name, status = await ServiceRegistry.check_health(service_data)
        assert status == ServiceStatus.UNHEALTHY
    finally:
        httpx.AsyncClient = original_client
