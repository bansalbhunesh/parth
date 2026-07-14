"""Redis-backed sliding-window limits for multi-replica deployments."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local reset = now + window
  if oldest[2] then reset = tonumber(oldest[2]) + window end
  return {0, count, reset}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window)
return {1, count + 1, now + window}
"""


class DistributedLimitUnavailable(RuntimeError):
    """The authoritative distributed limiter could not be reached."""


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    reset_at_ms: int
    degraded: bool = False


class RedisRateLimiter:
    def __init__(self, client: Any, prefix: str = "pramaan:rate") -> None:
        self._client = client
        self._prefix = prefix

    @classmethod
    def from_url(cls, url: str) -> "RedisRateLimiter":
        from redis import Redis

        return cls(Redis.from_url(url, decode_responses=False, socket_connect_timeout=1, socket_timeout=1))

    def check(
        self,
        identifier: str,
        bucket: str,
        limit: int,
        window_seconds: int = 3600,
        *,
        fail_closed: bool,
    ) -> RateLimitDecision:
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        member = f"{now_ms}:{time.time_ns()}"
        try:
            allowed, count, reset_at = self._client.eval(
                _SLIDING_WINDOW_SCRIPT,
                1,
                f"{self._prefix}:{bucket}:{identifier}",
                now_ms,
                window_ms,
                limit,
                member,
            )
        except Exception as exc:
            if fail_closed:
                raise DistributedLimitUnavailable("distributed rate limiter unavailable") from exc
            return RateLimitDecision(True, limit, now_ms + window_ms, degraded=True)
        return RateLimitDecision(bool(allowed), max(0, limit - int(count)), int(reset_at))
