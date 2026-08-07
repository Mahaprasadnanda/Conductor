import pytest
import asyncio
from httpx import AsyncClient
from fastapi import Response

@pytest.mark.asyncio
async def test_metrics_endpoint_and_counters(async_client: AsyncClient):
    from app.gateway.proxy.proxy import ProxyEngine
    
    # Mock proxy to simulate success
    async def mock_forward(context):
        import time
        context.metrics.upstream_latency = 0.015 # mock 15ms latency
        resp = Response(content="Proxied", status_code=200)
        context.fastapi_response = resp
        return resp

    original_forward = ProxyEngine.forward
    ProxyEngine.forward = mock_forward

    try:
        # Generate some traffic
        for _ in range(3):
            # This requires authentication because Gateway is protected by default
            # We'll just call a valid service endpoint using auth headers, or we can just bypass auth for the test
            # To make it simple, we'll authenticate and then call the gateway
            pass
            
        # Register a mock project and service and hit it to generate metrics
        admin_data = {"email": "admin_metrics@test.com", "password": "admin"}
        await async_client.post("/api/v1/auth/register", json=admin_data)
        login_res = await async_client.post("/api/v1/auth/login", data={"username": "admin_metrics@test.com", "password": "admin"})
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Create Project
        proj_res = await async_client.post("/api/v1/projects/", json={"name": "metrics_proj"}, headers=auth_headers)
        proj_id = proj_res.json()["id"]
        
        # Create Service
        svc_res = await async_client.post(f"/api/v1/services/?project_id={proj_id}", json={
            "service_name": "metrics_svc",
            "base_url": "http://metrics.internal",
            "is_active": True,
            "strip_path": True,
            "load_balancer_strategy": "ROUND_ROBIN"
        }, headers=auth_headers)
        svc_id = svc_res.json()["id"]
        
        # Create 2 Instances
        inst1 = await async_client.post(f"/api/v1/service-instances/", json={
            "service_id": svc_id,
            "base_url": "http://node-1.internal",
            "status": "Healthy"
        }, headers=auth_headers)
        assert inst1.status_code == 201
        
        inst2 = await async_client.post(f"/api/v1/service-instances/", json={
            "service_id": svc_id,
            "base_url": "http://node-2.internal",
            "status": "Healthy"
        }, headers=auth_headers)
        assert inst2.status_code == 201
        
        # Send 3 requests
        for _ in range(3):
            res = await async_client.get("/api/v1/gateway/metrics_svc/test", headers=auth_headers)
            assert res.status_code == 200
            
        # Now fetch /metrics
        metrics_res = await async_client.get("/metrics")
        assert metrics_res.status_code == 200
        assert "text/plain" in metrics_res.headers["content-type"]
        
        # Verify specific metrics exist in the payload
        payload = metrics_res.text
            
        # Requests total
        assert 'gateway_requests_total{method="GET",service_name="metrics_svc",status_code="200"}' in payload
        # Latency histograms
        assert 'gateway_request_latency_seconds_count{service_name="metrics_svc"}' in payload
        assert 'gateway_upstream_latency_seconds_count{service_name="metrics_svc"}' in payload
        # Load balancer
        assert 'gateway_lb_routing_total{' in payload
        assert 'strategy="ROUND_ROBIN"' in payload
        # Active connections
        assert 'gateway_active_connections{' in payload
        # Circuit breaker
        assert 'gateway_circuit_breaker_state{service_name="metrics_svc"}' in payload
        # Services / instances registered
        assert 'gateway_services_registered' in payload
        assert 'gateway_instances_registered' in payload
        
        # Test simulated proxy error
        async def mock_error_forward(context):
            from app.gateway.exceptions import ProxyException
            raise ProxyException("connection timeout")
            
        ProxyEngine.forward = mock_error_forward
        try:
            err_res = await async_client.get("/api/v1/gateway/metrics_svc/test", headers=auth_headers)
            # If the test client doesn't raise, check the status code
            assert err_res.status_code in (500, 502)
        except Exception:
            pass
            
        # Fetch metrics again
        metrics_res2 = await async_client.get("/metrics")
        payload2 = metrics_res2.text
        assert 'gateway_proxy_errors_total{error_type="timeout",service_name="metrics_svc"}' in payload2
        
        # Reset proxy forward to successful mock
        ProxyEngine.forward = mock_forward
        
        # Test rate limit hits
        # Set a very low rate limit for a new service
        svc2_res = await async_client.post(f"/api/v1/services/?project_id={proj_id}", json={
            "service_name": "rate_limited_svc",
            "base_url": "http://limited.internal",
            "is_active": True,
            "strip_path": True,
            "load_balancer_strategy": "ROUND_ROBIN"
        }, headers=auth_headers)
        svc2_id = svc2_res.json()["id"]
        
        # Create rate limit policy (1 request per minute)
        await async_client.post("/api/v1/rate-limits/", json={
            "service_id": svc2_id,
            "limit": 1,
            "window_seconds": 60,
            "algorithm": "SLIDING_WINDOW_LOG",
            "enabled": True
        }, headers=auth_headers)
        
        # Allow background task to sync cache
        await asyncio.sleep(1.2)
        
        # 1st request succeeds
        await async_client.get("/api/v1/gateway/rate_limited_svc/test", headers=auth_headers)
        # 2nd and 3rd requests fail with 429
        res429_1 = await async_client.get("/api/v1/gateway/rate_limited_svc/test", headers=auth_headers)
        res429_2 = await async_client.get("/api/v1/gateway/rate_limited_svc/test", headers=auth_headers)
        
        assert res429_1.status_code == 429
        assert res429_2.status_code == 429
        
        # Fetch metrics again
        metrics_res3 = await async_client.get("/metrics")
        payload3 = metrics_res3.text
        
        assert 'gateway_rate_limit_hits_total{service_name="rate_limited_svc"} 2.0' in payload3
        
        # Verify active connections returned to zero
        # We made requests to metrics_svc earlier, and rate_limited_svc. 
        # All requests have completed, so all instances should have 0 active connections.
        if 'gateway_active_connections{instance_id="' not in payload3:
            print("PAYLOAD 3:", payload3)
        assert 'gateway_active_connections{instance_id="' in payload3
        for line in payload3.splitlines():
            if line.startswith('gateway_active_connections{'):
                assert line.endswith('0.0')

        # Verify gauges reflect DB count (we created 2 services and 2 instances)
        assert 'gateway_services_registered 2.0' in payload3
        assert 'gateway_instances_registered 2.0' in payload3
        
    finally:
        ProxyEngine.forward = original_forward
