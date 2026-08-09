import pytest
import json
from unittest.mock import AsyncMock, patch
from app.gateway.middleware.logging import LoggingMiddleware
from app.gateway.context import RequestContext

@pytest.mark.asyncio
@patch('app.database.connection.redis_client', new_callable=AsyncMock)
async def test_logging_middleware_pushes_to_redis(mock_redis):
    
    context = RequestContext.create()
    context.request_id = "test-req-1"
    context.gateway.method = "GET"
    context.gateway.path = "/api/v1/test"
    context.gateway.client_ip = "127.0.0.1"
    context.gateway.response_status = 500
    context.gateway.response_size = 123
    context.metrics.latency = 0.5
    
    mw = LoggingMiddleware()
    await mw.after_response(context, None)
    
    # Needs to wait for the asyncio.create_task to run
    import asyncio
    await asyncio.sleep(0.1)
    
    # Assert lpush was called twice (once for recent_requests, once for recent_errors because status 500)
    assert mock_redis.lpush.call_count == 2
    assert mock_redis.ltrim.call_count == 2
    
    args = mock_redis.lpush.call_args_list[0][0]
    key = args[0]
    payload = json.loads(args[1])
    
    assert key == "gateway:recent_requests"
    assert payload["request_id"] == "test-req-1"
    assert payload["status_code"] == 500
