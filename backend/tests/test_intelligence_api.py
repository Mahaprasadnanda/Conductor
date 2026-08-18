import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.api.v1.intelligence.TrafficIntelligenceService.generate_overview")
async def test_get_overview_api(mock_generate, auth_headers):
    mock_generate.return_value = {
        "status": "HEALTHY",
        "active_anomaly_count": 0,
        "recent_anomalies": [],
        "recommendations": []
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Assuming project_id=1 exists for the auth user, wait no, ProjectService.get_project is real!
        # We need to mock ProjectService.get_project
        with patch("app.api.v1.intelligence.ProjectService.get_project"):
            response = await client.get("/api/v1/intelligence/overview?project_id=1", headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["active_anomaly_count"] == 0

@pytest.mark.asyncio
@patch("app.api.v1.intelligence.TrafficIntelligenceService.generate_overview")
async def test_get_anomalies_api(mock_generate, auth_headers):
    mock_generate.return_value = type('obj', (object,), {
        "status": "HEALTHY",
        "active_anomaly_count": 0,
        "recent_anomalies": [],
        "recommendations": []
    })
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.v1.intelligence.ProjectService.get_project"):
            response = await client.get("/api/v1/intelligence/anomalies?project_id=1", headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data

@pytest.mark.asyncio
@patch("app.api.v1.intelligence.TrafficIntelligenceService.generate_overview")
async def test_get_recommendations_api(mock_generate, auth_headers):
    mock_generate.return_value = type('obj', (object,), {
        "status": "HEALTHY",
        "active_anomaly_count": 0,
        "recent_anomalies": [],
        "recommendations": [{"title": "Test"}]
    })
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.v1.intelligence.ProjectService.get_project"):
            response = await client.get("/api/v1/intelligence/recommendations?project_id=1", headers=auth_headers)
        
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
