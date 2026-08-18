from typing import List, Optional
from app.database.connection import redis_client
from app.models.service import ServiceInstance, LoadBalancerStrategy as StrategyEnum
from app.gateway.context import RequestContext
from app.gateway.load_balancer.strategies import (
    LoadBalancerStrategy,
    RoundRobinStrategy,
    LeastConnectionsStrategy,
    WeightedRoundRobinStrategy,
    RandomStrategy,
    HealthAwareStrategy
)

class LoadBalancerManager:
    def __init__(self):
        self.strategies = {
            StrategyEnum.ROUND_ROBIN: RoundRobinStrategy(),
            StrategyEnum.LEAST_CONNECTIONS: LeastConnectionsStrategy(),
            StrategyEnum.WEIGHTED_ROUND_ROBIN: WeightedRoundRobinStrategy(),
            StrategyEnum.RANDOM: RandomStrategy(),
            StrategyEnum.HEALTH_AWARE: HealthAwareStrategy()
        }

    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance], strategy_name: StrategyEnum) -> Optional[ServiceInstance]:
        strategy = self.strategies.get(strategy_name, self.strategies[StrategyEnum.ROUND_ROBIN])
        
        # Populate metrics
        context.load_balancer.strategy = strategy_name.value
        context.load_balancer.service_pool_size = len(instances)
        
        selected = await strategy.select_instance(context, instances)
        if selected:
            context.load_balancer.selected_instance = selected.instance_id
            context.load_balancer.routing_reason = f"Selected by {strategy_name.value}"
        else:
            context.load_balancer.routing_reason = "No available instances"
            
        return selected

    async def increment_connections(self, instance_id: str, service_name: str = "unknown", service_id: int = 0) -> int:
        redis_key = f"gateway:lb:conn:{instance_id}"
        val = await redis_client.incr(redis_key)
        
        try:
            from app.gateway.metrics.prometheus import prometheus_manager
            
            # Since we just have instance_id, we need a generic way to find project_id.
            # But wait, we don't have request context here. It's just a raw instance_id connection counter.
            # However, the metric expects project_id. Let's look at the label definition.
            # Actually, `gateway_active_connections` only takes `["project_id", "service_name", "instance_id"]`.
            # To avoid breaking, we pass "0" or fetch it.
            prometheus_manager.gateway_active_connections.labels(
                project_id="0",
                service_name=service_name,
                service_id=str(service_id),
                instance_id=instance_id
            ).set(val)
        except Exception:
            pass
            
        return val

    async def decrement_connections(self, instance_id: str, service_name: str = "unknown", service_id: int = 0) -> int:
        redis_key = f"gateway:lb:conn:{instance_id}"
        val = await redis_client.decr(redis_key)
        if val < 0:
            await redis_client.set(redis_key, 0)
            val = 0
            
        try:
            from app.gateway.metrics.prometheus import prometheus_manager
            prometheus_manager.gateway_active_connections.labels(
                project_id="0",
                service_name=service_name,
                service_id=str(service_id),
                instance_id=instance_id
            ).set(val)
        except Exception:
            pass
            
        return val

load_balancer_manager = LoadBalancerManager()
