"""
TURBO-CDI API: Rate Limiter
API protection with sliding window
"""

import time
from typing import Dict
from collections import defaultdict


class RateLimiter:
    """Sliding window rate limiter."""

    def __init__(self):
        # requests per hour
        self.limits = {"free": 100, "basic": 1000, "pro": 10000, "enterprise": 100000}

        # In-memory storage (use Redis in production)
        self.requests: Dict[str, list] = defaultdict(list)
        self.hourly_counts: Dict[str, int] = defaultdict(int)

    async def check_limit(self, user_id: str, tier: str = "free") -> bool:
        """Check if user is within rate limit."""
        now = time.time()
        window = 3600  # 1 hour

        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] if now - req_time < window
        ]

        # Check limit
        limit = self.limits.get(tier, 100)
        if len(self.requests[user_id]) >= limit:
            return False

        # Record request
        self.requests[user_id].append(now)
        self.hourly_counts[user_id] += 1

        return True

    async def get_request_count(self, hours: int = 24) -> int:
        """Get total request count."""
        return sum(self.hourly_counts.values())
