import asyncio
import random
import httpx
from typing import Callable, Awaitable, Any
from app.gateway.exceptions import ProxyException

class RetryPolicy:
    @staticmethod
    def is_transient_failure(exception: Exception, response: Any = None) -> bool:
        if isinstance(exception, httpx.TimeoutException):
            return True
        if isinstance(exception, ProxyException):
            return True
        if isinstance(exception, httpx.RequestError):
            return True
        if response and hasattr(response, "status_code"):
            # Retry 5xx errors (except 501 Not Implemented, but typically 500, 502, 503, 504 are transient)
            if response.status_code in [500, 502, 503, 504]:
                return True
        return False

    @staticmethod
    async def execute(
        func: Callable[[], Awaitable[Any]],
        max_attempts: int,
        base_delay: float = 0.5,
        max_delay: float = 10.0,
        jitter: bool = True
    ) -> Any:
        attempts = 0
        while attempts <= max_attempts:
            try:
                response = await func()
                if RetryPolicy.is_transient_failure(None, response) and attempts < max_attempts:
                    # Treat response as a failure that needs retry
                    raise ProxyException(f"Transient HTTP error: {response.status_code}")
                return response, attempts
            except Exception as e:
                if not RetryPolicy.is_transient_failure(e) or attempts >= max_attempts:
                    raise e
                
                # Exponential backoff
                delay = min(base_delay * (2 ** attempts), max_delay)
                if jitter:
                    delay = delay * random.uniform(0.5, 1.5)
                
                attempts += 1
                await asyncio.sleep(delay)
        
        # Should not be reached
        raise Exception("Retry failed")
