from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

@dataclass
class AuthContext:
    authenticated_user: Optional[Any] = None

@dataclass
class GatewayContext:
    service_name: Optional[str] = None
    service_id: Optional[int] = None
    endpoint: Optional[str] = None
    method: str = ""
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    client_ip: Optional[str] = None
    response_status: Optional[int] = None
    response_size: Optional[int] = None

@dataclass
class MetricsContext:
    start_time: Optional[float] = None
    latency: Optional[float] = None
    gateway_latency: Optional[float] = None
    upstream_latency: Optional[float] = None
    selected_instance: Optional[str] = None
    retry_count: int = 0
    circuit_state: Optional[str] = None
    rate_limit_hit: bool = False
    middleware_timings: Dict[str, float] = field(default_factory=dict)
    request_completed: bool = False

@dataclass
class CustomContext:
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RateLimitContext:
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_time: Optional[float] = None
    allowed: Optional[bool] = None
    algorithm: Optional[str] = None
    policy_id: Optional[int] = None

@dataclass
class ResilienceContext:
    circuit_state: Optional[str] = None
    retry_count: int = 0
    timeout: Optional[float] = None
    fallback_used: bool = False
    failure_reason: Optional[str] = None
    policy_id: Optional[int] = None

@dataclass
class LoadBalancerContext:
    selected_instance: Optional[str] = None
    strategy: Optional[str] = None
    service_pool_size: int = 0
    active_connections: Optional[int] = None
    instance_latency: Optional[float] = None
    routing_reason: Optional[str] = None

@dataclass
class RequestContext:
    request_id: str
    trace_id: str
    correlation_id: str
    timestamp: datetime
    
    auth: AuthContext = field(default_factory=AuthContext)
    gateway: GatewayContext = field(default_factory=GatewayContext)
    metrics: MetricsContext = field(default_factory=MetricsContext)
    custom: CustomContext = field(default_factory=CustomContext)
    rate_limit: RateLimitContext = field(default_factory=RateLimitContext)
    resilience: ResilienceContext = field(default_factory=ResilienceContext)
    load_balancer: LoadBalancerContext = field(default_factory=LoadBalancerContext)

    # fastapi native objects if needed by proxy/middleware
    fastapi_request: Optional[Any] = None
    fastapi_response: Optional[Any] = None
    
    @classmethod
    def create(cls) -> "RequestContext":
        # Generate initial IDs, they may be overwritten by RequestIdMiddleware if headers are present
        req_id = str(uuid.uuid4())
        return cls(
            request_id=req_id,
            trace_id=req_id,
            correlation_id=req_id,
            timestamp=datetime.utcnow()
        )
