"""Code-level safety checks that run before the agent sees a message."""

import re
import time
from collections import defaultdict, deque

# Card numbers (13-19 digits, optional spaces/dashes) and US SSNs.
CARD_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_pii(text: str) -> tuple[str, bool]:
    """Mask payment-card and SSN-like numbers so they never reach the model, the DB history, or the audit log."""
    redacted = CARD_RE.sub("[REDACTED CARD NUMBER]", text)
    redacted = SSN_RE.sub("[REDACTED SSN]", redacted)
    return redacted, redacted != text


class RateLimiter:
    """Sliding-window limit per shopper key (user id or client IP); protects cost and abuse."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max = max_requests
        self.window = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max:
            return False
        q.append(now)
        return True


chat_limiter = RateLimiter(max_requests=15, window_seconds=60)
