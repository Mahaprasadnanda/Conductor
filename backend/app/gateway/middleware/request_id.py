import uuid
from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext

class RequestIdMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        # Check if client provided X-Request-ID
        client_req_id = context.gateway.headers.get("x-request-id")
        
        if client_req_id:
            context.request_id = client_req_id
            context.trace_id = client_req_id
            context.correlation_id = client_req_id
        
        # We ensure it's in the headers for downstream services
        context.gateway.headers["x-request-id"] = context.request_id

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        # FastAPI handles response headers, we inject the X-Request-ID into the actual FastAPI response
        if context.fastapi_response:
            context.fastapi_response.headers["x-request-id"] = context.request_id
