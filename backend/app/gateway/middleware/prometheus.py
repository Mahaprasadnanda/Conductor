from typing import Callable, Awaitable, Any, Optional
from fastapi import Response
import time

from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.metrics.prometheus import prometheus_manager

class PrometheusMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass

    async def dispatch(self, context: RequestContext, call_next: Callable[..., Awaitable[Any]]) -> Response:
        from prometheus_client import REGISTRY
        from app.core.logger import log
        import os
        
        log.info("PrometheusMiddleware_Debug", 
                 pid=os.getpid(),
                 registry_id=id(REGISTRY), 
                 manager_id=id(prometheus_manager),
                 counter_id=id(prometheus_manager.gateway_requests_total))
        
        prometheus_manager.gateway_inflight_requests.inc()
        response = None
        try:
            response = await call_next()
            return response
        except Exception as e:
            # record error type
            error_type = "proxy_exception"
            if "timeout" in str(e).lower():
                error_type = "timeout"
            elif "connection" in str(e).lower():
                error_type = "connection_error"
            service_data = context.custom.metadata.get("service_data", {})
            project_id = str(service_data.get("project_id", "0"))
            service_id = str(service_data.get("id", "0"))
                
            prometheus_manager.gateway_proxy_errors_total.labels(
                project_id=project_id,
                service_name=context.gateway.service_name or "unknown",
                service_id=service_id,
                error_type=error_type
            ).inc()
            raise
        finally:
            try:
                prometheus_manager.gateway_inflight_requests.dec()
                
                service_name = context.gateway.service_name or "unknown"
                service_data = context.custom.metadata.get("service_data", {})
                project_id = str(service_data.get("project_id", "0"))
                service_id = str(service_data.get("id", "0"))
                
                # Status code
                status_code = context.gateway.response_status
                if status_code is None:
                    if response and hasattr(response, "status_code"):
                        status_code = response.status_code
                    else:
                        status_code = 500
                        
                # Check for 5xx errors from upstream
                if status_code >= 500:
                    prometheus_manager.gateway_proxy_errors_total.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id,
                        error_type="upstream_5xx"
                    ).inc()
                        
                # Method
                method = context.gateway.method or "UNKNOWN"
                
                # Record total requests
                prometheus_manager.gateway_requests_total.labels(
                    project_id=project_id,
                    service_name=service_name,
                    service_id=service_id,
                    method=method,
                    status_code=str(status_code)
                ).inc()
                
                log.info("PrometheusMiddleware_Success", 
                         service_name=service_name, 
                         method=method, 
                         status_code=str(status_code),
                         msg="Incremented gateway_requests_total successfully")
                
                # Request latency (gateway + upstream)
                if context.metrics.latency is not None:
                    prometheus_manager.gateway_request_latency_seconds.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id
                    ).observe(context.metrics.latency)
                    
                # Upstream latency
                if context.metrics.upstream_latency is not None:
                    prometheus_manager.gateway_upstream_latency_seconds.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id
                    ).observe(context.metrics.upstream_latency)
                    
                # Resilience retries
                if context.resilience.retry_count > 0:
                    prometheus_manager.gateway_retries_total.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id
                    ).inc(context.resilience.retry_count)
                    
                # Circuit breaker state
                if context.resilience.circuit_state:
                    state_val = 0
                    if context.resilience.circuit_state == "HALF_OPEN":
                        state_val = 1
                    elif context.resilience.circuit_state == "OPEN":
                        state_val = 2
                    prometheus_manager.gateway_circuit_breaker_state.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id
                    ).set(state_val)
                    
                # Load balancer routing
                if context.load_balancer.selected_instance and context.load_balancer.strategy:
                    prometheus_manager.gateway_lb_routing_total.labels(
                        project_id=project_id,
                        service_name=service_name,
                        service_id=service_id,
                        instance_id=context.load_balancer.selected_instance,
                        strategy=context.load_balancer.strategy
                    ).inc()
                    
                # Middleware timings
                for mw_name, timing in context.metrics.middleware_timings.items():
                    prometheus_manager.gateway_middleware_execution_seconds.labels(
                        middleware_name=mw_name
                    ).observe(timing)
                    
            except Exception as metric_error:
                # Safely catch any prometheus metric collection errors
                from app.core.logger import log
                log.error("Prometheus metrics error", error=str(metric_error))
