from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class SimpleRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> RateLimitResult:
        now = time.monotonic()
        with self._lock:
            window_start, count = self._buckets.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start = now
                count = 0

            if count >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - window_start)))
                self._buckets[key] = (window_start, count)
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

            self._buckets[key] = (window_start, count + 1)
            return RateLimitResult(allowed=True, retry_after_seconds=0)

