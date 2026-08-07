from typing import Callable, Awaitable, Any, Optional
from fastapi import Response
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.exceptions import ServiceUnavailableException
from app.gateway.load_balancer.manager import load_balancer_manager
from app.repositories.service_instance import service_instance_repo
from app.database.connection import async_session_maker
from app.models.service import LoadBalancerStrategy as StrategyEnum
import time

class LoadBalancerMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        pass

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass

    async def dispatch(self, context: RequestContext, call_next: Callable[[], Awaitable[Response]]) -> Response:
        if not context.gateway.service_id:
            # Skip if no service id
            return await call_next()
            
        strategy = context.custom.metadata.get("service_data", {}).get("load_balancer_strategy", "ROUND_ROBIN")
        strategy_enum = StrategyEnum(strategy)
        
        # Get instances from DB
        async with async_session_maker() as db:
            instances = await service_instance_repo.get_by_service_id(db, context.gateway.service_id)
            
        if not instances:
            # If no instances, fallback to the service's base_url
            return await call_next()
            
        # Select instance
        start_time = time.time()
        selected_instance = await load_balancer_manager.select_instance(context, instances, strategy_enum)
        
        if not selected_instance:
            raise ServiceUnavailableException(f"No available instances for service {context.gateway.service_name}")
            
        context.load_balancer.instance_latency = (time.time() - start_time) * 1000  # ms
        
        # Override target base url
        context.custom.metadata["target_base_url"] = selected_instance.base_url
        
        # Increment active connections
        context.load_balancer.active_connections = await load_balancer_manager.increment_connections(
            selected_instance.instance_id,
            service_name=context.gateway.service_name or "unknown"
        )
        
        try:
            # Proceed with request
            response = await call_next()
            
            # Inject headers
            if context.fastapi_response:
                context.fastapi_response.headers["X-Service-Instance"] = str(selected_instance.instance_id)
                context.fastapi_response.headers["X-LoadBalancer-Strategy"] = str(strategy_enum.value)
                
            return response
        finally:
            # Decrement active connections
            await load_balancer_manager.decrement_connections(
                selected_instance.instance_id,
                service_name=context.gateway.service_name or "unknown"
            )
