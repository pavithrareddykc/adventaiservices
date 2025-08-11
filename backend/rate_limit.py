import os
import time
from collections import deque
from threading import Lock
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._ip_to_timestamps: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def allow(self, ip_address: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            dq = self._ip_to_timestamps.get(ip_address)
            if dq is None:
                dq = deque()
                self._ip_to_timestamps[ip_address] = dq
            # prune old
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) < self.max_requests:
                dq.append(now)
                return True
            return False


def build_default_rate_limiter() -> RateLimiter:
    max_req = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
    window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    return RateLimiter(max_requests=max_req, window_seconds=window)