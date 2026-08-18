from typing import Optional, Any
import time
from sqlalchemy.future import select
from sqlalchemy import or_, and_

from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.rate_limiter import SlidingWindowLogStrategy
from app.database.connection import get_redis, get_db_session
from app.models.rate_limit import RateLimitPolicy
from app.gateway.exceptions import RateLimitException
from app.config.settings import settings
from app.core.logger import log

class RateLimiterMiddleware(BaseMiddleware):
    def __init__(self):
        self.strategy = SlidingWindowLogStrategy()

    async def _get_policy(self, service_id: Optional[int], endpoint: str) -> dict:
        from app.database.connection import async_session_maker
        async with async_session_maker() as session:
            result = await session.execute(
                select(RateLimitPolicy).where(
                    RateLimitPolicy.enabled == True,
                    or_(
                        and_(RateLimitPolicy.service_id == service_id, RateLimitPolicy.endpoint_path == endpoint),
                        and_(RateLimitPolicy.service_id == service_id, RateLimitPolicy.endpoint_path.is_(None)),
                        and_(RateLimitPolicy.service_id.is_(None), RateLimitPolicy.endpoint_path == endpoint),
                        and_(RateLimitPolicy.service_id.is_(None), RateLimitPolicy.endpoint_path.is_(None))
                    )
                )
            )
            policies = result.scalars().all()
            
            import structlog
            log = structlog.get_logger()
            log.info("RateLimiter Debug", service_id=service_id, endpoint=endpoint, policies_found=len(policies))
            
            for p in policies:
                log.info("RateLimiter Policy Debug", p_id=p.id, p_svc_id=p.service_id, p_ep=p.endpoint_path)
                if p.service_id == service_id and p.endpoint_path == endpoint:
                    return {"id": p.id, "limit": p.limit, "window": p.window_seconds, "algo": p.algorithm.value}
            
            for p in policies:
                if p.service_id == None and p.endpoint_path == endpoint:
                    return {"id": p.id, "limit": p.limit, "window": p.window_seconds, "algo": p.algorithm.value}
                    
            for p in policies:
                if p.service_id == service_id and p.endpoint_path == None:
                    return {"id": p.id, "limit": p.limit, "window": p.window_seconds, "algo": p.algorithm.value}
                    
            for p in policies:
                if p.service_id == None and p.endpoint_path == None:
                    return {"id": p.id, "limit": p.limit, "window": p.window_seconds, "algo": p.algorithm.value}

        return {
            "id": None, 
            "limit": settings.DEFAULT_RATE_LIMIT, 
            "window": settings.DEFAULT_WINDOW_SECONDS, 
            "algo": "SLIDING_WINDOW_LOG"
        }

    async def before_request(self, context: RequestContext) -> None:
        service_name = context.gateway.service_name
        service_id = context.gateway.service_id
        endpoint = context.gateway.path
        
        if endpoint and not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        
        try:
            from prometheus_client import REGISTRY
            from app.core.logger import log
            from app.gateway.metrics.prometheus import prometheus_manager
            log.info("RateLimiterMiddleware_Debug", 
                     registry_id=id(REGISTRY), 
                     manager_id=id(prometheus_manager),
                     counter_id=id(prometheus_manager.gateway_requests_total))
        except:
            pass

        user_id = context.auth.authenticated_user
        
        policy = await self._get_policy(service_id, endpoint)
        
        if user_id and endpoint:
            key = f"ratelimit:usr:{user_id}:svc:{service_id}:ep:{endpoint}"
        elif user_id and service_id:
            key = f"ratelimit:usr:{user_id}:svc:{service_id}"
        elif user_id:
            key = f"ratelimit:usr:{user_id}:global"
        elif endpoint:
            key = f"ratelimit:anon:svc:{service_id}:ep:{endpoint}"
        elif service_id:
            key = f"ratelimit:anon:svc:{service_id}"
        else:
            key = "ratelimit:global"
            
        current_time = time.time()
        redis = get_redis()
        
        try:
            result = await self.strategy.is_allowed(
                redis=redis,
                key=key,
                limit=policy["limit"],
                window_seconds=policy["window"],
                current_time=current_time
            )
            
            context.rate_limit.limit = policy["limit"]
            context.rate_limit.remaining = result.remaining
            context.rate_limit.reset_time = result.reset_time
            context.rate_limit.allowed = result.allowed
            context.rate_limit.algorithm = policy["algo"]
            context.rate_limit.policy_id = policy["id"]
        except Exception as e:
            log.warning("redis_rate_limit_failure", error=str(e), action="failing_open")
            context.rate_limit.limit = policy["limit"]
            context.rate_limit.remaining = 1
            context.rate_limit.reset_time = current_time
            context.rate_limit.allowed = True
            context.rate_limit.algorithm = policy["algo"]
            context.rate_limit.policy_id = policy["id"]
            
            # Since it failed open, skip the block below by setting a dummy result
            class DummyResult:
                allowed = True
                remaining = 1
                reset_time = current_time
            result = DummyResult()
        
        log.info("RateLimiterMiddleware Debug", extra={
            "service_id": service_id,
            "endpoint": endpoint,
            "policy": policy,
            "redis_key": key,
            "limit": policy["limit"],
            "remaining": result.remaining,
            "allowed": result.allowed
        })
        
        if not result.allowed:
            retry_after = max(0, int(result.reset_time - current_time))
            headers = {
                "X-RateLimit-Limit": str(policy["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(result.reset_time)),
                "Retry-After": str(retry_after)
            }
            
            # Record prometheus metric before throwing
            from app.gateway.metrics.prometheus import prometheus_manager
            
            service_data = context.custom.metadata.get("service_data", {})
            project_id = str(service_data.get("project_id", "0"))
            
            prometheus_manager.gateway_rate_limit_hits_total.labels(
                project_id=project_id,
                service_name=service_name or "unknown",
                service_id=str(service_id) if service_id else "0"
            ).inc()
            
            raise RateLimitException(headers=headers)

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        if response and hasattr(response, "headers"):
            if context.rate_limit.limit is not None:
                response.headers["X-RateLimit-Limit"] = str(context.rate_limit.limit)
            if context.rate_limit.remaining is not None:
                response.headers["X-RateLimit-Remaining"] = str(context.rate_limit.remaining)
            if context.rate_limit.reset_time is not None:
                response.headers["X-RateLimit-Reset"] = str(int(context.rate_limit.reset_time))
