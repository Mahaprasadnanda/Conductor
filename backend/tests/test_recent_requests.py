import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.gateway.middleware.logging import LoggingMiddleware
from app.gateway.context import RequestContext
from app.services.analytics_service import AnalyticsService

@pytest.mark.asyncio
@patch('app.database.connection.redis_client', new_callable=AsyncMock)
@patch('app.services.analytics_service.redis_client', new_callable=AsyncMock)
async def test_recent_requests_success(mock_redis_analytics, mock_redis_conn):
    # Test A: Successful request
    context = RequestContext.create()
    context.request_id = "test-req-succ"
    context.gateway.method = "GET"
    context.gateway.path = "/api/v1/test"
    context.gateway.client_ip = "127.0.0.1"
    context.gateway.response_status = 200
    context.gateway.service_name = "test-service"
    context.gateway.service_id = 10
    context.custom.metadata["service_data"] = {"project_id": 4}
    
    mw = LoggingMiddleware()
    await mw.after_response(context, None)
    
    # Should push once to recent_requests, not recent_errors (200)
    assert mock_redis_conn.lpush.call_count == 1
    args = mock_redis_conn.lpush.call_args_list[0][0]
    assert args[0] == "gateway:recent_requests"
    
    payload = json.loads(args[1])
    assert payload["request_id"] == "test-req-succ"
    assert payload["status_code"] == 200
    assert payload["project_id"] == 4
    assert payload["service_name"] == "test-service"
    assert payload["service_id"] == 10
    assert "timestamp" in payload
    
    # Mock fetching
    mock_redis_analytics.lrange.return_value = [json.dumps(payload)]
    
    db_mock = MagicMock()
    with patch.object(AnalyticsService, 'get_project_services', return_value=[{"id": 10, "service_name": "test-service"}]):
        results = await AnalyticsService.get_recent_requests(db_mock, 4)
        assert len(results) == 1
        assert results[0]["request_id"] == "test-req-succ"

@pytest.mark.asyncio
@patch('app.database.connection.redis_client', new_callable=AsyncMock)
@patch('app.services.analytics_service.redis_client', new_callable=AsyncMock)
async def test_recent_requests_error(mock_redis_analytics, mock_redis_conn):
    # Test B: Error request
    context = RequestContext.create()
    context.request_id = "test-req-err"
    context.gateway.response_status = 502
    context.gateway.service_name = "test-err"
    context.custom.metadata["service_data"] = {"project_id": 4}
    
    mw = LoggingMiddleware()
    await mw.after_response(context, None)
    
    assert mock_redis_conn.lpush.call_count == 2
    args_err = mock_redis_conn.lpush.call_args_list[1][0]
    assert args_err[0] == "gateway:recent_errors"
    payload = json.loads(args_err[1])
    assert payload["status_code"] == 502
    
    mock_redis_analytics.lrange.return_value = [json.dumps(payload)]
    
    db_mock = MagicMock()
    with patch.object(AnalyticsService, 'get_project_services', return_value=[{"id": 11, "service_name": "test-err"}]):
        results = await AnalyticsService.get_recent_errors(db_mock, 4)
        assert len(results) == 1
        assert results[0]["status_code"] == 502

@pytest.mark.asyncio
@patch('app.database.connection.redis_client', new_callable=AsyncMock)
@patch('app.services.analytics_service.redis_client', new_callable=AsyncMock)
async def test_redis_failure(mock_redis_analytics, mock_redis_conn):
    # Test C: Redis failure
    mock_redis_conn.lpush.side_effect = Exception("Redis is down")
    
    context = RequestContext.create()
    context.request_id = "test-redis-fail"
    context.gateway.response_status = 200
    
    mw = LoggingMiddleware()
    # Should not raise exception
    await mw.after_response(context, None)
    
    # Same for fetch
    mock_redis_analytics.lrange.side_effect = Exception("Redis is down")
    db_mock = MagicMock()
    with patch.object(AnalyticsService, 'get_project_services', return_value=[{"id": 1}]):
        results = await AnalyticsService.get_recent_requests(db_mock, 4)
        assert results == []

@pytest.mark.asyncio
@patch('app.database.connection.redis_client', new_callable=AsyncMock)
@patch('app.services.analytics_service.redis_client', new_callable=AsyncMock)
async def test_project_isolation(mock_redis_analytics, mock_redis_conn):
    # Test D: Project isolation
    req_a = {"project_id": 4, "request_id": "A"}
    req_b = {"project_id": 5, "request_id": "B"}
    
    mock_redis_analytics.lrange.return_value = [json.dumps(req_a), json.dumps(req_b)]
    
    db_mock = MagicMock()
    with patch.object(AnalyticsService, 'get_project_services', return_value=[{"id": 1}]):
        # Fetch for project 4
        results_4 = await AnalyticsService.get_recent_requests(db_mock, 4)
        assert len(results_4) == 1
        assert results_4[0]["request_id"] == "A"
        
        # Fetch for project 5
        results_5 = await AnalyticsService.get_recent_requests(db_mock, 5)
        assert len(results_5) == 1
        assert results_5[0]["request_id"] == "B"

