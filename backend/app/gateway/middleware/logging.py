from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.core.logger import log

class LoggingMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        latency_str = f"{context.metrics.latency:.4f}s" if context.metrics.latency is not None else "unknown"
        
        status_code = context.gateway.response_status
        if status_code is None:
            if response and hasattr(response, "status_code"):
                status_code = response.status_code
            else:
                status_code = 500

        project_id = context.custom.metadata.get("service_data", {}).get("project_id")

        log_data = {
            "request_id": context.request_id,
            "trace_id": context.trace_id,
            "project_id": project_id,
            "service_id": context.gateway.service_id,
            "service_name": context.gateway.service_name,
            "endpoint": context.gateway.endpoint,
            "method": context.gateway.method,
            "path": context.gateway.path,
            "client_ip": context.gateway.client_ip,
            "status_code": status_code,
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
        
        from app.database.connection import redis_client
        import json
        from datetime import datetime, timezone
        
        if redis_client:
            try:
                log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
                data_str = json.dumps(log_data)
                
                await redis_client.lpush("gateway:recent_requests", data_str)
                await redis_client.ltrim("gateway:recent_requests", 0, 199)
                
                if status_code and status_code >= 400:
                    await redis_client.lpush("gateway:recent_errors", data_str)
                    await redis_client.ltrim("gateway:recent_errors", 0, 199)
            except Exception as e:
                log.error("redis_log_push_error", error=str(e), request_id=context.request_id, service_name=context.gateway.service_name)
