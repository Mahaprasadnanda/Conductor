from typing import Dict, Type
from app.gateway.middleware.base import BaseMiddleware

_registry: Dict[str, Type[BaseMiddleware]] = {}

def register_middleware(name: str, middleware_class: Type[BaseMiddleware]):
    _registry[name] = middleware_class

def get_middleware(name: str) -> BaseMiddleware:
    if name not in _registry:
        from app.gateway.exceptions import MiddlewareException
        raise MiddlewareException(f"Middleware {name} not found in registry")
    return _registry[name]()

# Import built-ins
from app.gateway.middleware.request_id import RequestIdMiddleware
from app.gateway.middleware.authentication import AuthenticationMiddleware
from app.gateway.middleware.timing import TimingMiddleware
from app.gateway.middleware.logging import LoggingMiddleware
from app.gateway.middleware.rate_limiter import RateLimiterMiddleware
from app.gateway.middleware.placeholders import (
    CircuitBreakerMiddleware,
    RetryMiddleware,
    CacheMiddleware,
    AdaptiveRoutingMiddleware
)

# Register built-ins
register_middleware("request_id", RequestIdMiddleware)
register_middleware("authentication", AuthenticationMiddleware)
register_middleware("timing", TimingMiddleware)
register_middleware("logging", LoggingMiddleware)
register_middleware("rate_limiter", RateLimiterMiddleware)
register_middleware("circuit_breaker", CircuitBreakerMiddleware)
register_middleware("retry", RetryMiddleware)
register_middleware("cache", CacheMiddleware)
register_middleware("adaptive_routing", AdaptiveRoutingMiddleware)
