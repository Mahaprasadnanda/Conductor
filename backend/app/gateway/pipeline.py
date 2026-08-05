from typing import List, Callable, Awaitable, Any, Optional
from app.gateway.context import RequestContext
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.middleware.registry import get_middleware
from app.core.logger import log

DEFAULT_MIDDLEWARE_ORDER = [
    "request_id",
    "authentication",
    "rate_limiter",
    "logging",
    "timing"
]

class GatewayPipeline:
    def __init__(self, middleware_names: List[str] = DEFAULT_MIDDLEWARE_ORDER):
        self.middlewares: List[BaseMiddleware] = [
            get_middleware(name) for name in middleware_names
        ]

    # Lifecycle hooks
    async def on_request_start(self, context: RequestContext) -> None:
        pass

    async def on_before_proxy(self, context: RequestContext) -> None:
        pass

    async def on_after_proxy(self, context: RequestContext, response: Optional[Any]) -> None:
        pass

    async def on_request_end(self, context: RequestContext) -> None:
        pass

    async def execute(self, context: RequestContext, proxy_func: Callable[[RequestContext], Awaitable[Any]]) -> Any:
        await self.on_request_start(context)
        response = None
        executed_middlewares = []
        
        try:
            for mw in self.middlewares:
                await mw.before_request(context)
                executed_middlewares.append(mw)
                
            await self.on_before_proxy(context)
            response = await proxy_func(context)
            await self.on_after_proxy(context, response)
            return response
        finally:
            # Execute after_response in reverse order
            for mw in reversed(executed_middlewares):
                try:
                    await mw.after_response(context, response)
                except Exception as e:
                    log.error("middleware_after_response_error", middleware=mw.__class__.__name__, error=str(e))
                    
            await self.on_request_end(context)
