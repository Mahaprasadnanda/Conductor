import pytest
from unittest.mock import patch
from app.services.traffic_intelligence import TrafficIntelligenceService
from app.schemas.intelligence import SeverityEnum

@pytest.mark.asyncio
@patch("app.services.traffic_intelligence.AnalyticsService.query_prometheus")
async def test_analyze_traffic_spikes(mock_query):
    # Mock current traffic higher than baseline
    async def mock_query_prometheus(query):
        if "avg_over_time" in query: # baseline
            return [{"metric": {"service_name": "demo"}, "value": [1000, "10.0"]}]
        else: # current
            return [{"metric": {"service_name": "demo"}, "value": [1000, "25.0"]}]
            
    mock_query.side_effect = mock_query_prometheus
    
    anomalies = await TrafficIntelligenceService.analyze_traffic_spikes("service_name=~'demo'")
    
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "Traffic Spike"
    assert anomalies[0].service_name == "demo"
    assert anomalies[0].current_value == 25.0
    assert anomalies[0].baseline_value == 10.0
    assert anomalies[0].severity == SeverityEnum.WARNING

@pytest.mark.asyncio
@patch("app.services.traffic_intelligence.AnalyticsService.query_prometheus")
async def test_analyze_error_spikes(mock_query):
    async def mock_query_prometheus(query):
        if "avg_over_time" in query:
            if "status_code" in query: # err base
                return [{"metric": {"service_name": "demo"}, "value": [1000, "1.0"]}]
            else: # tot base
                return [{"metric": {"service_name": "demo"}, "value": [1000, "100.0"]}]
        else:
            if "status_code" in query: # err curr
                return [{"metric": {"service_name": "demo"}, "value": [1000, "25.0"]}]
            else: # tot curr
                return [{"metric": {"service_name": "demo"}, "value": [1000, "100.0"]}]
                
    mock_query.side_effect = mock_query_prometheus
    
    anomalies = await TrafficIntelligenceService.analyze_error_spikes("service_name=~'demo'")
    
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "Error Spike"
    assert anomalies[0].severity == SeverityEnum.CRITICAL
    assert anomalies[0].current_value == 25.0 # 25%

@pytest.mark.asyncio
@patch("app.services.traffic_intelligence.AnalyticsService.query_prometheus")
async def test_analyze_rate_limits(mock_query):
    mock_query.return_value = [{"metric": {"service_name": "demo"}, "value": [1000, "15.0"]}]
    
    anomalies = await TrafficIntelligenceService.analyze_rate_limits("service_name=~'demo'")
    
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "Rate-Limit Spike"
    assert anomalies[0].current_value == 15.0

@pytest.mark.asyncio
@patch("app.services.traffic_intelligence.AnalyticsService.get_project_services", return_value=[{"id": 1, "service_name": "demo"}])
@patch("app.services.traffic_intelligence.AnalyticsService.query_prometheus")
async def test_generate_overview(mock_query, mock_services):
    mock_query.return_value = [] # no traffic -> no anomalies
    
    db_mock = type('db', (object,), {})()
    overview = await TrafficIntelligenceService.generate_overview(db_mock, 1)
    
    assert overview.status == "HEALTHY"
    assert overview.active_anomaly_count == 0
    assert len(overview.recent_anomalies) == 0
