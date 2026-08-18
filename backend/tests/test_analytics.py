import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.analytics_service import AnalyticsService
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.service import Service, ServiceInstance, ServiceStatus

@pytest.mark.asyncio
@patch('app.services.analytics_service.AnalyticsService.query_prometheus', return_value=[{"value": [1234, "42"]}])
async def test_analytics_service_mock_overview(mock_query):
    db_mock = MagicMock()
    
    # We need to mock two db.execute calls: one for Service, one for ServiceInstance
    mock_res_service = MagicMock()
    mock_res_service.scalars().all.return_value = [
        Service(id=1, service_name="svc1", project_id=1, status=ServiceStatus.HEALTHY, base_url="http://test")
    ]
    
    mock_res_instance = MagicMock()
    mock_res_instance.scalars().all.return_value = [
        ServiceInstance(id=1, service_id=1, status=ServiceStatus.HEALTHY)
    ]
    
    db_mock.execute = AsyncMock(side_effect=[mock_res_service, mock_res_instance])
    
    overview = await AnalyticsService.get_overview(db_mock, 1)
    assert overview["active_connections"] == 42.0
    assert overview["requests_per_second"] == 42.0
    assert overview["healthy_instances"] == 1.0
    assert overview["healthy_services"] == 1.0

@pytest.mark.asyncio
@patch('app.services.analytics_service.AnalyticsService.query_prometheus', return_value=[{"value": [1234, "42"]}])
async def test_analytics_service_external_service_healthy_instances(mock_query):
    db_mock = MagicMock()
    
    mock_res_service = MagicMock()
    # No explicit instances in DB, but it's an external service with a base_url
    mock_res_service.scalars().all.return_value = [
        Service(id=1, service_name="external-svc", project_id=1, status=ServiceStatus.HEALTHY, base_url="https://httpbin.org")
    ]
    
    mock_res_instance = MagicMock()
    mock_res_instance.scalars().all.return_value = []
    
    db_mock.execute = AsyncMock(side_effect=[mock_res_service, mock_res_instance])
    
    overview = await AnalyticsService.get_overview(db_mock, 1)
    assert overview["healthy_instances"] == 1.0
    assert overview["healthy_services"] == 1.0

@pytest.mark.asyncio
@patch.object(AnalyticsService, 'get_project_services', return_value=[{"id": 1, "service_name": "svc1"}])
@patch.object(AnalyticsService, 'query_prometheus_range', return_value=[
    {"values": [[1700000000, "10"], [1700000015, "15"]]}
])
async def test_analytics_timeseries(mock_query, mock_services):
    db_mock = MagicMock()
    ts = await AnalyticsService.get_timeseries(db_mock, 1, "1h")
    assert len(ts["traffic"]) == 2
    assert ts["traffic"][0]["value"] == 10.0
    assert ts["traffic"][1]["value"] == 15.0

@pytest.mark.asyncio
async def test_analytics_api_cross_tenant_isolation(auth_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/overview?project_id=9999", headers=auth_headers)
    assert response.status_code == 404
