from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.core.logger import log

class LoggingMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        latency_str = f"{context.metrics.latency:.4f}s" if context.metrics.latency is not None else "unknown"
        
        log_data = {
            "request_id": context.request_id,
            "trace_id": context.trace_id,
            "service_name": context.gateway.service_name,
            "endpoint": context.gateway.endpoint,
            "method": context.gateway.method,
            "path": context.gateway.path,
            "client_ip": context.gateway.client_ip,
            "status_code": context.gateway.response_status,
            "latency": latency_str,
            "response_size": context.gateway.response_size,
            "rl_policy_id": context.rate_limit.policy_id,
            "rl_algorithm": context.rate_limit.algorithm,
            "rl_allowed": context.rate_limit.allowed,
            "rl_limit": context.rate_limit.limit,
            "rl_remaining": context.rate_limit.remaining,
            "rl_reset_time": context.rate_limit.reset_time,
            "res_policy_id": context.resilience.policy_id,
            "res_circuit_state": context.resilience.circuit_state,
            "res_retry_count": context.resilience.retry_count,
            "res_timeout": context.resilience.timeout,
            "res_fallback_used": context.resilience.fallback_used,
            "res_failure_reason": context.resilience.failure_reason,
            "lb_strategy": context.load_balancer.strategy,
            "lb_service_pool_size": context.load_balancer.service_pool_size,
            "lb_selected_instance": context.load_balancer.selected_instance,
            "lb_active_connections": context.load_balancer.active_connections,
            "lb_instance_latency": context.load_balancer.instance_latency,
            "lb_routing_reason": context.load_balancer.routing_reason
        }
        
        log.info("proxy_request", **log_data)
        
        # Asynchronously push to Redis for recent activity dashboard
        import asyncio
        from app.database.connection import redis_client
        import json
        from datetime import datetime, timezone
        
        async def push_to_redis():
            try:
                # Need timestamp
                log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
                data_str = json.dumps(log_data)
                
                # Push to recent requests
                await redis_client.lpush("gateway:recent_requests", data_str)
                await redis_client.ltrim("gateway:recent_requests", 0, 199)
                
                # Push to recent errors if error
                if context.gateway.response_status and context.gateway.response_status >= 400:
                    await redis_client.lpush("gateway:recent_errors", data_str)
                    await redis_client.ltrim("gateway:recent_errors", 0, 199)
            except Exception as e:
                log.error("redis_log_push_error", error=str(e))
                
        asyncio.create_task(push_to_redis())
