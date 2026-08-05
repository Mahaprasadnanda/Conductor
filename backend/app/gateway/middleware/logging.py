from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.core.logger import log

class LoggingMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        latency_str = f"{context.metrics.latency:.4f}s" if context.metrics.latency is not None else "unknown"
        
        log.info(
            "proxy_request",
            request_id=context.request_id,
            trace_id=context.trace_id,
            service_name=context.gateway.service_name,
            endpoint=context.gateway.endpoint,
            method=context.gateway.method,
            path=context.gateway.path,
            client_ip=context.gateway.client_ip,
            status_code=context.gateway.response_status,
            latency=latency_str,
            response_size=context.gateway.response_size,
            rl_policy_id=context.rate_limit.policy_id,
            rl_algorithm=context.rate_limit.algorithm,
            rl_allowed=context.rate_limit.allowed,
            rl_limit=context.rate_limit.limit,
            rl_remaining=context.rate_limit.remaining,
            rl_reset_time=context.rate_limit.reset_time
        )
