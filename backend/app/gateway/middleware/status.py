from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.exceptions import ServiceUnavailableException
from app.gateway.cache import service_cache
from app.models.service import ServiceStatus

class StatusMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        if not context.gateway.service_name:
            return
            
        service_data = service_cache.get(context.gateway.service_name)
        if not service_data:
            return
            
        if service_data.get("status") not in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN]:
            context.gateway.response_status = 503
            context.resilience.failure_reason = "Service is Disabled"
            raise ServiceUnavailableException(f"Service is {service_data.get('status')}")

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass
