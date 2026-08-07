import pytest
import asyncio
from app.gateway.context import RequestContext, GatewayContext
from app.models.service import ServiceInstance, ServiceStatus, LoadBalancerStrategy
from app.gateway.load_balancer.strategies import (
    RoundRobinStrategy,
    LeastConnectionsStrategy,
    WeightedRoundRobinStrategy,
    RandomStrategy,
    HealthAwareStrategy
)
from app.database.connection import redis_client
import uuid
from datetime import datetime

@pytest.fixture
def mock_instances():
    return [
        ServiceInstance(id=1, service_id=1, instance_id=str(uuid.uuid4()), base_url="http://node1", weight=5, status=ServiceStatus.HEALTHY),
        ServiceInstance(id=2, service_id=1, instance_id=str(uuid.uuid4()), base_url="http://node2", weight=1, status=ServiceStatus.HEALTHY),
        ServiceInstance(id=3, service_id=1, instance_id=str(uuid.uuid4()), base_url="http://node3", weight=1, status=ServiceStatus.UNHEALTHY),
    ]

@pytest.fixture
def mock_context():
    return RequestContext(
        request_id="test",
        trace_id="test",
        correlation_id="test",
        timestamp=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_round_robin(mock_context, mock_instances):
    strategy = RoundRobinStrategy()
    
    # Reset index
    await redis_client.delete("gateway:lb:rr_index:1")
    
    selected1 = await strategy.select_instance(mock_context, mock_instances)
    assert selected1 == mock_instances[0]
    
    selected2 = await strategy.select_instance(mock_context, mock_instances)
    assert selected2 == mock_instances[1]
    
    selected3 = await strategy.select_instance(mock_context, mock_instances)
    assert selected3 == mock_instances[2]
    
    selected4 = await strategy.select_instance(mock_context, mock_instances)
    assert selected4 == mock_instances[0]

@pytest.mark.asyncio
async def test_least_connections(mock_context, mock_instances):
    strategy = LeastConnectionsStrategy()
    
    # Set connections
    await redis_client.set(f"gateway:lb:conn:{mock_instances[0].instance_id}", 10)
    await redis_client.set(f"gateway:lb:conn:{mock_instances[1].instance_id}", 5)
    await redis_client.set(f"gateway:lb:conn:{mock_instances[2].instance_id}", 10)
    
    selected = await strategy.select_instance(mock_context, mock_instances)
    assert selected == mock_instances[1]

@pytest.mark.asyncio
async def test_weighted_round_robin(mock_context, mock_instances):
    strategy = WeightedRoundRobinStrategy()
    
    # Reset swrr state
    await redis_client.delete("gateway:lb:swrr:1")
    
    # Weights: node1(5), node2(1), node3(1)
    # Expected sequence over 7 requests: node1, node1, node1, node2, node1, node3, node1 (or similar distribution)
    
    selections = []
    for _ in range(7):
        selected = await strategy.select_instance(mock_context, mock_instances)
        selections.append(selected.id)
        
    assert selections.count(1) == 5
    assert selections.count(2) == 1
    assert selections.count(3) == 1

@pytest.mark.asyncio
async def test_health_aware(mock_context, mock_instances):
    strategy = HealthAwareStrategy()
    
    # Reset RR index
    await redis_client.delete("gateway:lb:rr_index:1")
    
    selected1 = await strategy.select_instance(mock_context, mock_instances)
    assert selected1.status == ServiceStatus.HEALTHY
    
    selected2 = await strategy.select_instance(mock_context, mock_instances)
    assert selected2.status == ServiceStatus.HEALTHY
    
    # Node 3 is unhealthy, so it should only bounce between node 1 and 2
    assert selected1.id != selected2.id
    assert selected1.id in (1, 2)
    assert selected2.id in (1, 2)
