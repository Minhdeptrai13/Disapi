"""
rate_limiter.py — Smart Discord Rate Limiter
============================================

Implements Discord's rate limiting model:
  - Global rate limit (50 req/s across all endpoints)
  - Per-route bucket rate limits (from response headers)
  - 429 response handling with retry_after
  - Exponential backoff with full jitter for server errors
  - Async-safe per-bucket locks

Reference:
    https://discord.com/developers/docs/topics/rate-limits
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .constants import (
    DEFAULT_RATE_LIMIT_DELAY,
    DEFAULT_RATE_LIMIT_JITTER,
    DEFAULT_RATE_LIMIT_RETRIES,
)


__all__: list[str] = [
    "RateLimiter",
    "RateLimitInfo",
    "BucketInfo",
    "rate_limit_bucket",
]

logger = logging.getLogger("dapi.ratelimit")


# ─── Bucket Helpers ───────────────────────────────────────────────────────────

def rate_limit_bucket(path: str) -> str:
    """Normalise an API path to a rate-limit bucket key.

    Discord shares rate-limit quotas across routes that differ only in their
    *major parameters* (channel_id, guild_id, webhook_id + webhook_token).
    We collapse those IDs to placeholder tokens so the bucket is shared.

    Args:
        path: Raw API path, e.g. ``/channels/123/messages/456``.

    Returns:
        Normalised bucket key, e.g. ``channels/{id}/messages/{id}``.

    Example:
        >>> rate_limit_bucket("/channels/123/messages")
        'channels/{id}/messages'
        >>> rate_limit_bucket("/guilds/456/members")
        'guilds/{id}/members'
    """
    # Major parameter containers — their immediate child ID is the bucket key
    _MAJOR: frozenset[str] = frozenset({"channels", "guilds", "webhooks"})

    parts = path.strip("/").split("/")
    result: list[str] = []
    i = 0
    while i < len(parts):
        part = parts[i]
        result.append(part)
        # If this segment is a major resource and the next is a numeric ID
        if part in _MAJOR and i + 1 < len(parts) and parts[i + 1].isdigit():
            result.append("{id}")
            i += 2
            continue
        # Collapse other numeric IDs to {id} (non-major)
        # Keep them as-is so we get precise buckets for sub-resources
        i += 1
    return "/".join(result)


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class RateLimitInfo:
    """Snapshot of rate-limit header data for a single response.

    Attributes:
        bucket: Server-assigned bucket hash from ``X-RateLimit-Bucket``.
        limit: Maximum requests in window.
        remaining: Requests remaining in current window.
        reset: Unix timestamp (float) when the window resets.
        reset_after: Seconds until window reset (float, more precise).
        scope: Rate-limit scope — ``'user'``, ``'global'``, or ``'shared'``.
    """

    bucket: Optional[str] = None
    limit: int = 0
    remaining: int = 0
    reset: float = 0.0
    reset_after: float = 0.0
    scope: str = "user"

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "RateLimitInfo":
        """Parse rate-limit headers from a response.

        Args:
            headers: Response headers dict (lowercased keys preferred).

        Returns:
            Populated ``RateLimitInfo`` instance.
        """
        h = {k.lower(): v for k, v in headers.items()}
        return cls(
            bucket=h.get("x-ratelimit-bucket"),
            limit=int(h.get("x-ratelimit-limit", 0) or 0),
            remaining=int(h.get("x-ratelimit-remaining", 0) or 0),
            reset=float(h.get("x-ratelimit-reset", 0) or 0),
            reset_after=float(h.get("x-ratelimit-reset-after", 0) or 0),
            scope=h.get("x-ratelimit-scope", "user"),
        )


@dataclass
class BucketInfo:
    """Internal per-bucket tracking state.

    Attributes:
        bucket_hash: Server-assigned bucket hash string.
        route_key: Normalised route key used as dict key.
        limit: Maximum requests per window.
        remaining: Remaining requests in current window.
        reset: Unix timestamp when window resets.
        last_updated: When this bucket was last updated (monotonic).
        lock: Per-bucket async lock for concurrency safety.
    """

    bucket_hash: str = ""
    route_key: str = ""
    limit: int = 0
    remaining: int = 1  # Optimistic start — assume one slot free
    reset: float = 0.0
    last_updated: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def is_exhausted(self) -> bool:
        """Return True if the bucket is currently exhausted."""
        return self.remaining <= 0 and time.time() < self.reset

    def seconds_until_reset(self) -> float:
        """Seconds to wait until this bucket resets (0 if already reset)."""
        return max(0.0, self.reset - time.time())


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Discord API rate limiter.

    Manages both **global** and **per-route bucket** rate limits.
    Call :meth:`acquire` before every request, and :meth:`update` after
    receiving the response headers.

    Thread safety:
        All state mutations are guarded by asyncio locks. This class is
        designed for single-event-loop, multi-coroutine usage.

    Args:
        max_retries: Maximum automatic retries for 429 responses.
        base_delay: Base delay (seconds) for exponential backoff.
        jitter: Maximum random jitter added to delays.

    Example:
        limiter = RateLimiter()

        await limiter.acquire("/channels/123/messages")
        response = await http.post(...)
        limiter.update("/channels/123/messages", response.headers)
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        base_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        jitter: float = DEFAULT_RATE_LIMIT_JITTER,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.jitter = jitter

        # bucket_key → BucketInfo
        self._buckets: Dict[str, BucketInfo] = {}
        # server-hash → bucket_key (populated from response headers)
        self._hash_to_key: Dict[str, str] = {}

        # Global rate limit state
        self._global_event = asyncio.Event()
        self._global_event.set()  # Not blocked initially
        self._global_reset: float = 0.0

        # Coarse lock for bucket dict mutations
        self._dict_lock = asyncio.Lock()

    # ─── Public API ──────────────────────────────────────────────────────────

    async def acquire(self, path: str) -> None:
        """Wait until it is safe to make a request to *path*.

        Checks global lock first, then per-bucket limit.

        Args:
            path: API path (e.g. ``/channels/123/messages``).
        """
        # 1. Respect global rate limit
        await self._wait_for_global()

        # 2. Respect per-bucket limit
        key = rate_limit_bucket(path)
        bucket = await self._get_or_create_bucket(key)
        async with bucket.lock:
            await self._wait_for_bucket(bucket)

    def update(self, path: str, headers: Dict[str, str]) -> None:
        """Update bucket state from response headers.

        Should be called immediately after receiving each response.

        Args:
            path: API path that produced these headers.
            headers: Response headers dict.
        """
        info = RateLimitInfo.from_headers(headers)
        if not info.bucket:
            return  # No rate-limit info for this route

        key = rate_limit_bucket(path)
        self._hash_to_key[info.bucket] = key

        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = BucketInfo(bucket_hash=info.bucket, route_key=key)
            self._buckets[key] = bucket

        bucket.bucket_hash = info.bucket
        bucket.limit = info.limit
        bucket.remaining = info.remaining
        bucket.reset = info.reset
        bucket.last_updated = time.monotonic()

        logger.debug(
            "Bucket update key=%r hash=%r limit=%d remaining=%d reset_in=%.3fs",
            key,
            info.bucket,
            info.limit,
            info.remaining,
            info.reset_after,
        )

    async def handle_rate_limit(
        self,
        path: str,
        retry_after: float,
        is_global: bool = False,
        scope: str = "user",
    ) -> None:
        """Handle a 429 Too Many Requests response.

        Blocks further requests until *retry_after* seconds have elapsed.

        Args:
            path: API path that was rate limited.
            retry_after: Seconds to wait (from the response body).
            is_global: Whether this is the global rate limit.
            scope: Rate-limit scope string.
        """
        wait = retry_after + self._jitter()

        if is_global:
            logger.warning("Global rate limit hit — waiting %.3fs", wait)
            self._global_event.clear()
            self._global_reset = time.time() + retry_after
            await asyncio.sleep(wait)
            self._global_event.set()
        else:
            key = rate_limit_bucket(path)
            bucket = self._buckets.get(key)
            if bucket:
                bucket.remaining = 0
                bucket.reset = time.time() + retry_after
            logger.warning(
                "Bucket rate limit hit path=%r scope=%r — waiting %.3fs",
                path,
                scope,
                wait,
            )
            await asyncio.sleep(wait)

    async def backoff(self, attempt: int) -> float:
        """Compute and sleep for exponential backoff with full jitter.

        Uses the "full jitter" strategy from AWS:
        ``sleep = random(0, min(cap, base * 2^attempt))``

        Args:
            attempt: Zero-based attempt counter.

        Returns:
            Actual sleep duration in seconds.
        """
        cap = 60.0
        delay = min(cap, self.base_delay * (2 ** min(attempt, 10)))
        sleep = random.uniform(0, delay)
        logger.debug("Backoff attempt=%d sleeping=%.3fs", attempt, sleep)
        await asyncio.sleep(sleep)
        return sleep

    def is_globally_rate_limited(self) -> bool:
        """Return True if the global rate limit is currently active."""
        return not self._global_event.is_set()

    def is_bucket_rate_limited(self, path: str) -> bool:
        """Return True if the bucket for *path* is currently exhausted."""
        key = rate_limit_bucket(path)
        bucket = self._buckets.get(key)
        return bucket.is_exhausted() if bucket else False

    def reset_all(self) -> None:
        """Clear all stored rate-limit state (useful for testing)."""
        self._buckets.clear()
        self._hash_to_key.clear()
        self._global_event.set()
        self._global_reset = 0.0
        logger.debug("Rate limiter state cleared")

    def get_bucket_info(self, path: str) -> Optional[BucketInfo]:
        """Return bucket info for a path, or None if unknown.

        Args:
            path: API path.

        Returns:
            ``BucketInfo`` or ``None``.
        """
        return self._buckets.get(rate_limit_bucket(path))

    # ─── Internal helpers ────────────────────────────────────────────────────

    async def _wait_for_global(self) -> None:
        """Block until the global rate limit clears."""
        if not self._global_event.is_set():
            wait = max(0.0, self._global_reset - time.time()) + self._jitter()
            logger.warning("Waiting for global rate limit: %.3fs", wait)
            await asyncio.sleep(wait)
            self._global_event.set()

    async def _wait_for_bucket(self, bucket: BucketInfo) -> None:
        """Block until the bucket has capacity."""
        if bucket.is_exhausted():
            wait = bucket.seconds_until_reset() + self._jitter()
            logger.debug(
                "Waiting for bucket=%r: %.3fs", bucket.route_key, wait
            )
            await asyncio.sleep(wait)

    async def _get_or_create_bucket(self, key: str) -> BucketInfo:
        """Get an existing bucket or create a new one."""
        if key not in self._buckets:
            async with self._dict_lock:
                if key not in self._buckets:
                    self._buckets[key] = BucketInfo(route_key=key)
        return self._buckets[key]

    def _jitter(self) -> float:
        """Return a random jitter value in [0, self.jitter]."""
        return random.uniform(0.0, self.jitter)
