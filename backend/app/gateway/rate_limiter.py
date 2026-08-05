from abc import ABC, abstractmethod
from typing import Tuple, Optional
from redis.asyncio import Redis

class RateLimitResult:
    def __init__(self, allowed: bool, remaining: int, reset_time: float):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_time = reset_time

class RateLimiterStrategy(ABC):
    @abstractmethod
    async def is_allowed(
        self, 
        redis: Redis, 
        key: str, 
        limit: int, 
        window_seconds: int,
        current_time: float
    ) -> RateLimitResult:
        pass

class SlidingWindowLogStrategy(RateLimiterStrategy):
    # Atomic Lua script for sliding window log using Redis Sorted Sets
    LUA_SCRIPT = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])
    local member_id = ARGV[4]

    local window_start = current_time - window
    redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
    
    local current_count = redis.call('ZCARD', key)
    if current_count >= limit then
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local reset_time = current_time + window
        if oldest and #oldest > 1 then
            reset_time = tonumber(oldest[2]) + window
        end
        return {0, limit - current_count, reset_time}
    end

    redis.call('ZADD', key, current_time, member_id)
    redis.call('EXPIRE', key, window)
    return {1, limit - current_count - 1, current_time + window}
    """

    def __init__(self):
        self._script = None

    async def is_allowed(
        self, 
        redis: Redis, 
        key: str, 
        limit: int, 
        window_seconds: int,
        current_time: float
    ) -> RateLimitResult:
        
        import uuid
        try:
            if self._script is None or getattr(self._script, 'registered_client', None) != redis:
                self._script = redis.register_script(self.LUA_SCRIPT)
                self._script.registered_client = redis
                
            member_id = f"{current_time}:{uuid.uuid4().hex}"
            result = await self._script(
                keys=[key],
                args=[limit, window_seconds, current_time, member_id]
            )
            
            allowed = bool(result[0])
            remaining = max(0, int(result[1]))
            reset_time = float(result[2])
            return RateLimitResult(allowed=allowed, remaining=remaining, reset_time=reset_time)
        except Exception as e:
            from app.core.logger import log
            log.warning("redis_rate_limit_error", error=str(e), key=key)
            # Fail-Open
            return RateLimitResult(allowed=True, remaining=limit, reset_time=current_time + window_seconds)

class SlidingWindowCounterStrategy(RateLimiterStrategy):
    async def is_allowed(self, redis: Redis, key: str, limit: int, window_seconds: int, current_time: float) -> RateLimitResult:
        raise NotImplementedError()

class TokenBucketStrategy(RateLimiterStrategy):
    async def is_allowed(self, redis: Redis, key: str, limit: int, window_seconds: int, current_time: float) -> RateLimitResult:
        raise NotImplementedError()

class FixedWindowStrategy(RateLimiterStrategy):
    async def is_allowed(self, redis: Redis, key: str, limit: int, window_seconds: int, current_time: float) -> RateLimitResult:
        raise NotImplementedError()

class AdaptiveStrategy(RateLimiterStrategy):
    async def is_allowed(self, redis: Redis, key: str, limit: int, window_seconds: int, current_time: float) -> RateLimitResult:
        raise NotImplementedError()
