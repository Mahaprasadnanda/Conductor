import time
from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext

class TimingMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        context.metrics.start_time = time.perf_counter()

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        if context.metrics.start_time is not None:
            latency = time.perf_counter() - context.metrics.start_time
            context.metrics.latency = latency
