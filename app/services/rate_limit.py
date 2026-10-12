import math
import threading
import time

from app.config import settings


class TokenBucketLimiter:
    """Allow short bursts, but cap the sustained rate per key.

    Each key starts with `burst` tokens. A request spends one token; tokens
    refill at `per_second`. With no tokens left the request is refused.
    In-memory, so it is per-process (a real deployment would use Redis).
    """

    def __init__(self, burst: int, per_second: float):
        self.burst = burst
        self.per_second = per_second
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> int | None:
        """Spend a token. Return None if allowed, else seconds until retry."""
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.burst), now))
            tokens = min(float(self.burst), tokens + (now - last) * self.per_second)
            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return None
            self._buckets[key] = (tokens, now)
            return max(1, math.ceil((1 - tokens) / self.per_second))

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


ip_limiter = TokenBucketLimiter(settings.rate_limit_ip_burst, settings.rate_limit_ip_per_second)
widget_limiter = TokenBucketLimiter(settings.rate_limit_widget_burst, settings.rate_limit_widget_per_second)