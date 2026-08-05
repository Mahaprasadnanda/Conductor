import time
from typing import Optional
from redis.asyncio import Redis

CB_BEFORE_SCRIPT = """
local state = redis.call('HGET', KEYS[1], 'state') or 'CLOSED'
local open_until = tonumber(redis.call('HGET', KEYS[1], 'open_until') or '0')
local current_time = tonumber(ARGV[1])
local half_open_limit = tonumber(ARGV[2])

if state == 'OPEN' then
    if current_time >= open_until then
        redis.call('HSET', KEYS[1], 'state', 'HALF_OPEN')
        redis.call('HSET', KEYS[1], 'half_open_count', '1')
        return 'HALF_OPEN'
    else
        return 'OPEN'
    end
end

if state == 'HALF_OPEN' then
    local count = tonumber(redis.call('HGET', KEYS[1], 'half_open_count') or '0')
    if count >= half_open_limit then
        -- Reject if we're already testing max allowed requests concurrently
        return 'OPEN'
    else
        redis.call('HINCRBY', KEYS[1], 'half_open_count', 1)
        return 'HALF_OPEN'
    end
end

return 'CLOSED'
"""

CB_SUCCESS_SCRIPT = """
redis.call('HSET', KEYS[1], 'state', 'CLOSED')
redis.call('HSET', KEYS[1], 'failures', '0')
redis.call('HSET', KEYS[1], 'half_open_count', '0')
return 'CLOSED'
"""

CB_FAILURE_SCRIPT = """
local state = redis.call('HGET', KEYS[1], 'state') or 'CLOSED'
local current_time = tonumber(ARGV[1])
local recovery_timeout = tonumber(ARGV[2])
local threshold = tonumber(ARGV[3])

if state == 'HALF_OPEN' then
    redis.call('HSET', KEYS[1], 'state', 'OPEN')
    redis.call('HSET', KEYS[1], 'open_until', tostring(current_time + recovery_timeout))
    return 'OPEN'
else
    local failures = redis.call('HINCRBY', KEYS[1], 'failures', 1)
    if failures >= threshold then
        redis.call('HSET', KEYS[1], 'state', 'OPEN')
        redis.call('HSET', KEYS[1], 'open_until', tostring(current_time + recovery_timeout))
        return 'OPEN'
    end
    return 'CLOSED'
end
"""

class CircuitBreakerPolicy:
    def __init__(self, redis: Redis):
        self.redis = redis
        # Register scripts for performance
        self._before_script = self.redis.register_script(CB_BEFORE_SCRIPT)
        self._success_script = self.redis.register_script(CB_SUCCESS_SCRIPT)
        self._failure_script = self.redis.register_script(CB_FAILURE_SCRIPT)

    async def check_state(self, service_id: int, half_open_requests: int) -> str:
        key = f"circuit_breaker:svc:{service_id}"
        current_time = int(time.time())
        state = await self._before_script(
            keys=[key],
            args=[current_time, half_open_requests]
        )
        return state.decode('utf-8') if isinstance(state, bytes) else state

    async def record_success(self, service_id: int) -> None:
        key = f"circuit_breaker:svc:{service_id}"
        await self._success_script(keys=[key])

    async def record_failure(self, service_id: int, failure_threshold: int, recovery_timeout: int) -> str:
        key = f"circuit_breaker:svc:{service_id}"
        current_time = int(time.time())
        state = await self._failure_script(
            keys=[key],
            args=[current_time, recovery_timeout, failure_threshold]
        )
        return state.decode('utf-8') if isinstance(state, bytes) else state
