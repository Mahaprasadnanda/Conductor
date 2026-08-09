import pytest
from unittest.mock import patch
from app.services.analytics_service import AnalyticsService

@pytest.mark.asyncio
async def test_get_time_params():
    start, end, step = AnalyticsService.get_time_params("5m")
    assert step == "15s"
    assert float(end) - float(start) == 300 # 5 minutes

    start, end, step = AnalyticsService.get_time_params("1h")
    assert step == "1m"
    assert float(end) - float(start) == 3600 # 1 hour

@pytest.mark.asyncio
@patch.object(AnalyticsService, 'query_prometheus', return_value=[{"value": [1234, "42"]}])
async def test_analytics_service_mock_overview(mock_query):
    overview = await AnalyticsService.get_overview()
    assert overview["active_connections"] == 42.0
    assert overview["healthy_instances"] == 42.0
    assert overview["requests_per_second"] == 42.0
    
@pytest.mark.asyncio
@patch.object(AnalyticsService, 'query_prometheus', return_value=[])
async def test_analytics_service_degraded_state(mock_query):
    overview = await AnalyticsService.get_overview()
    assert overview["active_connections"] == 0.0
    assert overview["requests_per_second"] == 0.0

@pytest.mark.asyncio
@patch.object(AnalyticsService, 'query_prometheus_range', return_value=[
    {"values": [[1700000000, "10"], [1700000015, "15"]]}
])
async def test_analytics_timeseries(mock_query):
    ts = await AnalyticsService.get_timeseries("1h")
    assert len(ts["traffic"]) == 2
    assert ts["traffic"][0]["value"] == 10.0
    assert ts["traffic"][1]["value"] == 15.0
