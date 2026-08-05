from typing import Callable, Awaitable, Any, Optional
from sqlalchemy.future import select
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.resilience.manager import ResilienceManager
from app.models.resilience import ResiliencePolicy
from app.database.connection import async_session_maker

class ResilienceMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass

    async def _get_policy(self, service_id: int) -> Optional[dict]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(ResiliencePolicy).where(ResiliencePolicy.service_id == service_id)
            )
            policy = result.scalars().first()
            if policy:
                return {
                    "id": policy.id,
                    "failure_threshold": policy.failure_threshold,
                    "recovery_timeout": policy.recovery_timeout,
                    "half_open_requests": policy.half_open_requests,
                    "retry_attempts": policy.retry_attempts,
                    "request_timeout": policy.request_timeout,
                    "fallback_enabled": policy.fallback_enabled,
                    "fallback_response": policy.fallback_response
                }
            return None

    async def dispatch(self, context: RequestContext, call_next: Callable[[], Awaitable[Any]]) -> Any:
        service_id = context.gateway.service_id
        if not service_id:
            return await call_next()
            
        policy = await self._get_policy(service_id)
        if not policy:
            return await call_next()
            
        context.resilience.policy_id = policy["id"]
        from app.gateway.resilience.timeout import TimeoutPolicy
        TimeoutPolicy.apply(context, policy["request_timeout"])
        
        try:
            response = await ResilienceManager.execute(context, policy, call_next)
            
            # Inject headers
            if response and hasattr(response, "headers"):
                if context.resilience.circuit_state:
                    response.headers["X-Circuit-State"] = context.resilience.circuit_state
                response.headers["X-Retry-Count"] = str(context.resilience.retry_count)
                
            return response
        except Exception as e:
            raise e
