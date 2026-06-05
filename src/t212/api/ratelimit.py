from __future__ import annotations
import asyncio
import random
import time
from dataclasses import dataclass


@dataclass
class _Bucket:
    capacity: float
    per_seconds: float
    tokens: float
    updated: float


class RateLimitGovernor:
    """Per-endpoint token bucket; honours server x-ratelimit-reset; jittered waits."""

    def __init__(self, limits, *, clock=time.monotonic, sleep=asyncio.sleep, rng=random.random, jitter=0.25):
        now = clock()
        self._buckets = {k: _Bucket(c, s, c, now) for k, (c, s) in limits.items()}
        self._clock = clock
        self._sleep = sleep
        self._rng = rng
        self._jitter = jitter
        self._reset_until: dict[str, float] = {}

    def _refill(self, b: _Bucket, now: float) -> None:
        elapsed = max(0.0, now - b.updated)
        b.tokens = min(b.capacity, b.tokens + elapsed * (b.capacity / b.per_seconds))
        b.updated = now

    async def acquire(self, key: str) -> None:
        b = self._buckets[key]
        while True:
            now = self._clock()
            until = self._reset_until.get(key, 0.0)
            if until > now:
                await self._sleep(until - now)
                now = self._clock()
                self._reset_until.pop(key, None)
                b.tokens = b.capacity
                b.updated = now
            self._refill(b, now)
            if b.tokens >= 1.0:
                b.tokens -= 1.0
                return
            deficit = 1.0 - b.tokens
            wait = deficit * (b.per_seconds / b.capacity)
            await self._sleep(wait * (1.0 + self._rng() * self._jitter))

    def note_server_reset(self, key: str, seconds_from_now: float) -> None:
        self._reset_until[key] = self._clock() + max(0.0, seconds_from_now)
