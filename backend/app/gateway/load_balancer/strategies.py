from typing import List, Optional
from abc import ABC, abstractmethod
from app.models.service import ServiceInstance, ServiceStatus
from app.gateway.context import RequestContext
import random
from app.database.connection import redis_client

class LoadBalancerStrategy(ABC):
    @abstractmethod
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        pass

class RoundRobinStrategy(LoadBalancerStrategy):
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        if not instances:
            return None
        service_id = instances[0].service_id
        redis_key = f"gateway:lb:rr_index:{service_id}"
        
        # Atomically increment and get the current index
        idx = await redis_client.incr(redis_key)
        return instances[(idx - 1) % len(instances)]

class LeastConnectionsStrategy(LoadBalancerStrategy):
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        if not instances:
            return None
            
        # Get connections for all instances from redis
        # Default to 0 if not set
        pipeline = redis_client.pipeline()
        for inst in instances:
            pipeline.get(f"gateway:lb:conn:{inst.instance_id}")
        conn_results = await pipeline.execute()
        
        # Parse connection counts
        conns = []
        for i, res in enumerate(conn_results):
            c = int(res) if res else 0
            conns.append((c, instances[i]))
            
        # Find minimum connections
        min_conn = min(conns, key=lambda x: x[0])[0]
        
        # Tie-breaking logic:
        # If multiple instances have the same lowest active_connections:
        # - Prefer the healthiest instance.
        # - If still tied, use Round Robin among only the tied instances.
        
        tied = [c[1] for c in conns if c[0] == min_conn]
        if len(tied) == 1:
            return tied[0]
            
        # Tie-breaker 1: Health
        healthy_tied = [t for t in tied if t.status == ServiceStatus.HEALTHY]
        if healthy_tied:
            tied = healthy_tied
            
        if len(tied) == 1:
            return tied[0]
            
        # Tie-breaker 2: Round Robin among tied
        service_id = instances[0].service_id
        redis_key = f"gateway:lb:lc_tie_rr:{service_id}"
        idx = await redis_client.incr(redis_key)
        return tied[(idx - 1) % len(tied)]

class WeightedRoundRobinStrategy(LoadBalancerStrategy):
    # Smooth Weighted Round Robin
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        if not instances:
            return None
            
        service_id = instances[0].service_id
        
        # We need to maintain state for SWRR.
        # For each instance, we track its current_weight.
        # Redis Hash: gateway:lb:swrr:{service_id} -> field: instance_id, value: current_weight
        
        redis_key = f"gateway:lb:swrr:{service_id}"
        
        total_weight = 0
        best_instance = None
        max_current_weight = -float('inf')
        
        # Get all current weights from Redis
        current_weights_raw = await redis_client.hgetall(redis_key)
        
        # We use a Lua script to make the selection atomic across concurrent requests
        lua_script = """
        local key = KEYS[1]
        local instances = cjson.decode(ARGV[1])
        local total_weight = 0
        local max_current_weight = -math.huge
        local best_instance_idx = -1
        
        for i, inst in ipairs(instances) do
            local current_weight = tonumber(redis.call('HGET', key, inst.id) or '0')
            current_weight = current_weight + inst.weight
            total_weight = total_weight + inst.weight
            
            if current_weight > max_current_weight then
                max_current_weight = current_weight
                best_instance_idx = i
            end
            
            redis.call('HSET', key, inst.id, current_weight)
        end
        
        if best_instance_idx ~= -1 then
            local best_id = instances[best_instance_idx].id
            local best_current = tonumber(redis.call('HGET', key, best_id))
            redis.call('HSET', key, best_id, best_current - total_weight)
            return best_id
        end
        return nil
        """
        
        # Pass instance IDs and weights to Lua
        import json
        instances_data = [{"id": inst.instance_id, "weight": inst.weight} for inst in instances]
        
        selected_instance_id = await redis_client.eval(
            lua_script, 1, redis_key, json.dumps(instances_data)
        )
        
        if selected_instance_id:
            if isinstance(selected_instance_id, bytes):
                selected_instance_id = selected_instance_id.decode('utf-8')
            for inst in instances:
                if inst.instance_id == selected_instance_id:
                    return inst
                    
        # Fallback to random if script fails
        return random.choice(instances)

class RandomStrategy(LoadBalancerStrategy):
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        if not instances:
            return None
        return random.choice(instances)

class HealthAwareStrategy(LoadBalancerStrategy):
    def __init__(self):
        self.rr = RoundRobinStrategy()
        
    async def select_instance(self, context: RequestContext, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        # HealthAwareStrategy should automatically exclude UNHEALTHY instances
        # Also exclude OPEN Circuit Breaker instances
        
        healthy_instances = []
        for inst in instances:
            if inst.status != ServiceStatus.HEALTHY:
                continue
                
            # Check Circuit Breaker state
            cb_key = f"gateway:resilience:cb:{inst.service_id}:{inst.base_url}"
            cb_state = await redis_client.hget(cb_key, "state")
            if cb_state and cb_state.decode('utf-8') == "OPEN":
                continue
                
            healthy_instances.append(inst)
            
        if not healthy_instances:
            return None
            
        return await self.rr.select_instance(context, healthy_instances)
