import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_load_balancer_e2e(async_client: AsyncClient, auth_headers: dict):
    # 1. Create a Project
    res = await async_client.post("/api/v1/projects/", json={"name": "lb_test_project"}, headers=auth_headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    # 2. Create a Service
    service_payload = {
        "service_name": "lb_demo_service",
        "base_url": "http://placeholder",
        "health_check_path": "/health",
        "load_balancer_strategy": "ROUND_ROBIN"
    }
    res = await async_client.post(f"/api/v1/services/?project_id={project_id}", json=service_payload, headers=auth_headers)
    assert res.status_code == 201
    service_id = res.json()["id"]

    # 3. Create Service Instance A
    instance_a = {
        "service_id": service_id,
        "instance_id": "node-A",
        "base_url": "http://node-a-backend",
        "weight": 1
    }
    res = await async_client.post("/api/v1/service-instances/", json=instance_a, headers=auth_headers)
    assert res.status_code == 201

    # 4. Create Service Instance B
    instance_b = {
        "service_id": service_id,
        "instance_id": "node-B",
        "base_url": "http://node-b-backend",
        "weight": 1
    }
    res = await async_client.post("/api/v1/service-instances/", json=instance_b, headers=auth_headers)
    assert res.status_code == 201

    # 5. Send 4 Gateway requests to test Round Robin
    # Wait, the proxy will actually try to forward to http://node-a-backend
    # We might get a 502/ProxyException since that domain doesn't exist.
    # We can mock the proxy forward or just use a known test domain.
    # Actually, let's just see what headers we get back if we get a 502. 
    # Or better yet, we can mock ProxyEngine.forward.
    
    # Wait! In tests, httpx might just intercept or we can monkeypatch ProxyEngine
    # Let's import ProxyEngine and monkeypatch it so it returns a dummy response instead of failing
    from app.gateway.proxy.proxy import ProxyEngine
    from fastapi import Response
    
    async def mock_forward(context):
        resp = Response(content=f"Proxied to {context.custom.metadata.get('target_base_url')}", status_code=200)
        context.fastapi_response = resp
        return resp

    original_forward = ProxyEngine.forward
    ProxyEngine.forward = mock_forward

    try:
        nodes_hit = []
        for i in range(4):
            res = await async_client.get("/api/v1/gateway/lb_demo_service/hello", headers=auth_headers)
            try:
                assert res.status_code == 200
                assert "x-service-instance" in res.headers
                assert res.headers["x-loadbalancer-strategy"] == "ROUND_ROBIN"
            except Exception as e:
                with open("/tmp/err.txt", "w") as f:
                    import traceback
                    f.write(traceback.format_exc())
                raise e
            nodes_hit.append(res.headers["x-service-instance"])

        assert len(set(nodes_hit)) == 2
        assert nodes_hit[0] != nodes_hit[1]
        assert nodes_hit[0] == nodes_hit[2]
        assert nodes_hit[1] == nodes_hit[3]
    finally:
        ProxyEngine.forward = original_forward
