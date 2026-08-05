from typing import Callable, Awaitable, Any, Optional
from app.gateway.context import RequestContext
from app.gateway.resilience.circuit_breaker import CircuitBreakerPolicy
from app.gateway.resilience.retry import RetryPolicy
from app.gateway.resilience.fallback import FallbackPolicy
from app.database.connection import get_redis
from app.gateway.exceptions import ProxyException

class ResilienceManager:
    @staticmethod
    async def execute(
        context: RequestContext,
        policy: dict,
        call_next: Callable[[], Awaitable[Any]]
    ) -> Any:
        service_id = context.gateway.service_id
        if not service_id:
            # If no service ID is known, we can't use resilience properly
            return await call_next()

        redis = get_redis()
        cb = CircuitBreakerPolicy(redis)

        # 1. Circuit Breaker Check
        state = await cb.check_state(service_id, policy["half_open_requests"])
        context.resilience.circuit_state = state
        
        if state == "OPEN":
            if policy["fallback_enabled"] and policy["fallback_response"]:
                context.resilience.fallback_used = True
                # Construct and return fallback response
                return FallbackPolicy.execute(policy["fallback_response"])
            
            # If no fallback, fail fast
            context.resilience.failure_reason = "circuit_open"
            raise ProxyException("Circuit breaker is OPEN")

        # 2. Execute with Retry
        async def _execute_attempt():
            return await call_next()

        try:
            response, attempts = await RetryPolicy.execute(
                _execute_attempt,
                max_attempts=policy["retry_attempts"]
            )
            context.resilience.retry_count = attempts
            
            # 3. Record Success
            await cb.record_success(service_id)
            context.resilience.circuit_state = "CLOSED"
            return response
            
        except Exception as e:
            # Retry Policy exhausted or non-transient error
            context.resilience.failure_reason = str(e)
            
            # 4. Record Failure
            new_state = await cb.record_failure(
                service_id,
                policy["failure_threshold"],
                policy["recovery_timeout"]
            )
            context.resilience.circuit_state = new_state
            raise e
