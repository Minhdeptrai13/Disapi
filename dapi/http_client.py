"""
http_client.py — Async HTTP Client for Discord API
===================================================

Provides the core async HTTP transport layer using ``httpx``.

Features:
  - HTTP/2 support via httpx
  - Persistent connection pooling
  - Smart rate limiting (global + per-bucket)
  - Automatic retry with exponential backoff + jitter
  - Audit-log reason header encoding
  - Automatic nonce injection for messages
  - Proxy support
  - Multipart file upload
  - Full request/response debug logging
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from .constants import (
    API_BASE_URL,
    DEFAULT_RATE_LIMIT_RETRIES,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_RATE_LIMIT_DELAY,
    get_default_headers,
    get_super_properties,
)
from .exceptions import (
    BadRequest,
    Forbidden,
    NotFound,
    RateLimited,
    ServerError,
    Unauthorized,
    exception_from_response,
)
from .rate_limiter import RateLimiter, rate_limit_bucket
from .utils import generate_nonce


__all__: list[str] = ["HTTPClient", "Route"]

logger = logging.getLogger("dapi.http")


# ─── Route ────────────────────────────────────────────────────────────────────

class Route:
    """Represents a Discord API route with HTTP method and path.

    Automatically constructs the full URL and computes the rate-limit
    bucket key for the path.

    Args:
        method: HTTP method (``'GET'``, ``'POST'``, etc.).
        path: API path template, e.g. ``'/channels/{channel_id}/messages'``.
        **params: Format parameters to substitute into *path*.

    Attributes:
        method (str): HTTP method in uppercase.
        path (str): Resolved API path.
        url (str): Full URL including base.
        bucket_key (str): Normalised bucket key for rate limiting.

    Example:
        >>> r = Route('POST', '/channels/{channel_id}/messages', channel_id='123')
        >>> r.url
        'https://discord.com/api/v10/channels/123/messages'
    """

    __slots__ = ("method", "path", "url", "bucket_key")

    BASE = API_BASE_URL

    def __init__(self, method: str, path: str, **params: Any) -> None:
        self.method = method.upper()
        self.path = path.format_map(params) if params else path
        self.url = f"{self.BASE}{self.path}"
        self.bucket_key = rate_limit_bucket(self.path)

    def __repr__(self) -> str:
        return f"<Route {self.method} {self.path}>"

    def __str__(self) -> str:
        return f"{self.method} {self.url}"


# ─── HTTP Client ──────────────────────────────────────────────────────────────

class HTTPClient:
    """Async HTTP client for the Discord REST API.

    Wraps ``httpx.AsyncClient`` with Discord-specific logic:
    rate limiting, retries, realistic headers, and error parsing.

    Args:
        token: Discord user token.
        timeout: Request timeout in seconds.
        max_retries: Maximum retries for rate-limit and server errors.
        proxy: Optional proxy URL (e.g. ``'http://127.0.0.1:8080'``).
        build_number: Discord client build number for Super-Properties.

    Example:
        async with HTTPClient(token) as http:
            data = await http.request(Route('GET', '/users/@me'))
    """

    def __init__(
        self,
        token: str,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        proxy: Optional[str] = None,
        build_number: Optional[int] = None,
        fingerprint_rotation: bool = True,
        rotation_interval: int = 100,
    ) -> None:
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy = proxy
        self.fingerprint_rotation = fingerprint_rotation
        self.rotation_interval = rotation_interval

        self._rate_limiter = RateLimiter(max_retries=max_retries)
        self._session: Optional[httpx.AsyncClient] = None
        self._session_lock = asyncio.Lock()

        # Fingerprinting rotation
        self._request_count = 0
        self._super_properties = get_super_properties(build_number) if build_number else get_super_properties()
        self._fingerprint_pool: List[str] = []
        self._current_fingerprint_index = 0
        
        # Initialize fingerprint pool if rotation is enabled
        if self.fingerprint_rotation:
            self._initialize_fingerprint_pool(build_number)

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    async def _get_session(self) -> httpx.AsyncClient:
        """Return the shared httpx session, creating it on first call."""
        if self._session is None or self._session.is_closed:
            async with self._session_lock:
                if self._session is None or self._session.is_closed:
                    limits = httpx.Limits(
                        max_keepalive_connections=10,
                        max_connections=20,
                        keepalive_expiry=60.0,
                    )
                    transport = (
                        httpx.AsyncHTTPTransport(proxy=self.proxy)
                        if self.proxy
                        else None
                    )
                    self._session = httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout),
                        limits=limits,
                        http2=True,
                        follow_redirects=True,
                        **({"transport": transport} if transport else {}),
                    )
        return self._session

    def _initialize_fingerprint_pool(self, build_number: Optional[int] = None) -> None:
        """Initialize a pool of different fingerprints for rotation."""
        self._fingerprint_pool = [self._super_properties]
        # Generate additional fingerprints with slight variations
        for _ in range(4):  # Pool of 5 fingerprints
            self._fingerprint_pool.append(get_super_properties(build_number))
        self._current_fingerprint_index = 0
        logger.debug(f"Initialized fingerprint pool with {len(self._fingerprint_pool)} fingerprints")
    
    def _rotate_fingerprint(self) -> None:
        """Rotate to the next fingerprint in the pool."""
        if not self.fingerprint_rotation or not self._fingerprint_pool:
            return
        
        self._current_fingerprint_index = (self._current_fingerprint_index + 1) % len(self._fingerprint_pool)
        self._super_properties = self._fingerprint_pool[self._current_fingerprint_index]
        logger.debug(f"Rotated fingerprint to index {self._current_fingerprint_index}")
    
    async def close(self) -> None:
        """Close the underlying HTTP session and release connections."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()
            self._session = None
            logger.debug("HTTP session closed")

    async def __aenter__(self) -> "HTTPClient":
        await self._get_session()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ─── Header Building ─────────────────────────────────────────────────────

    def _build_headers(
        self,
        extra: Optional[Dict[str, str]] = None,
        reason: Optional[str] = None,
        refresh_fingerprint: bool = False,
    ) -> Dict[str, str]:
        """Assemble request headers.

        Args:
            extra: Additional headers to merge.
            reason: Audit-log reason (URL-encoded into X-Audit-Log-Reason).
            refresh_fingerprint: Regenerate UA / Super-Properties this call.

        Returns:
            Complete headers dict.
        """
        # Rotate fingerprint based on request count or explicit refresh
        self._request_count += 1
        if refresh_fingerprint or (self.fingerprint_rotation and self._request_count % self.rotation_interval == 0):
            self._rotate_fingerprint()

        headers = get_default_headers()
        headers["Authorization"] = self.token
        headers["X-Super-Properties"] = self._super_properties

        if extra:
            headers.update(extra)

        if reason:
            headers["X-Audit-Log-Reason"] = urllib.parse.quote(reason, safe="")

        return headers

    # ─── Core Request ────────────────────────────────────────────────────────

    async def request(
        self,
        route: Route,
        *,
        json_payload: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        reason: Optional[str] = None,
    ) -> Any:
        """Make an authenticated HTTP request to the Discord API.

        Handles rate limiting, automatic retries, and error parsing.

        Args:
            route: Target ``Route`` object.
            json_payload: JSON body to send (sets Content-Type automatically).
            data: Form-encoded data body.
            params: URL query parameters.
            files: Multipart file upload data.
            headers: Extra HTTP headers.
            reason: Audit-log reason string.

        Returns:
            Parsed JSON response (dict, list, or None for 204).

        Raises:
            RateLimited: If rate limit retries are exhausted.
            Unauthorized: If the token is invalid (401).
            Forbidden: If access is denied (403).
            NotFound: If the resource is missing (404).
            BadRequest: If the request body is invalid (400).
            ServerError: For 5xx errors after retries.
            HTTPException: For other HTTP errors.
        """
        session = await self._get_session()

        for attempt in range(self.max_retries + 1):
            # Acquire rate-limit slot
            await self._rate_limiter.acquire(route.path)

            req_headers = self._build_headers(
                extra=headers,
                reason=reason,
                refresh_fingerprint=(attempt > 0),
            )

            # Inject Content-Type for JSON
            if json_payload is not None:
                req_headers["Content-Type"] = "application/json"

            # Auto-inject nonce for message creation
            if (
                json_payload is not None
                and route.method == "POST"
                and "messages" in route.path
                and "nonce" not in json_payload
            ):
                json_payload = {**json_payload, "nonce": generate_nonce()}

            # Build kwargs
            req_kw: Dict[str, Any] = {"headers": req_headers}
            if params:
                req_kw["params"] = {k: v for k, v in params.items() if v is not None}
            if json_payload is not None:
                req_kw["json"] = json_payload
            elif files is not None:
                req_kw["files"] = files
                if data:
                    req_kw["data"] = data
            elif data is not None:
                req_kw["data"] = data

            logger.debug("→ %s %s (attempt %d)", route.method, route.url, attempt + 1)

            try:
                response = await session.request(
                    method=route.method,
                    url=route.url,
                    **req_kw,
                )
            except httpx.TimeoutException as exc:
                logger.warning("Timeout on %s (attempt %d): %s", route, attempt + 1, exc)
                if attempt < self.max_retries:
                    await self._rate_limiter.backoff(attempt)
                    continue
                raise exception_from_response(0, "Timeout", str(exc), route.method, route.url)
            except httpx.NetworkError as exc:
                logger.warning("Network error on %s (attempt %d): %s", route, attempt + 1, exc)
                if attempt < self.max_retries:
                    await self._rate_limiter.backoff(attempt)
                    continue
                raise exception_from_response(0, "NetworkError", str(exc), route.method, route.url)

            # Update rate-limit state from headers
            self._rate_limiter.update(route.path, dict(response.headers))

            status = response.status_code
            logger.debug("← %d %s", status, route.url)

            # ── Parse body ─────────────────────────────────────────────────
            body: Any = None
            if response.content:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        body = response.json()
                    except json.JSONDecodeError:
                        body = response.text
                else:
                    body = response.text

            # ── 204 No Content ─────────────────────────────────────────────
            if status == 204:
                return None

            # ── 2xx Success ────────────────────────────────────────────────
            if 200 <= status < 300:
                return body

            # ── 429 Rate Limited ───────────────────────────────────────────
            if status == 429:
                retry_after: float = 1.0
                is_global = False
                scope = "user"

                resp_headers = dict(response.headers)
                if isinstance(body, dict):
                    retry_after = float(body.get("retry_after", 1.0))
                    is_global = body.get("global", False)
                else:
                    retry_after = float(resp_headers.get("retry-after", 1.0))

                is_global = is_global or resp_headers.get("x-ratelimit-global", "").lower() == "true"
                scope = resp_headers.get("x-ratelimit-scope", "user")

                logger.warning(
                    "429 Rate Limited on %s — retry_after=%.3fs global=%s scope=%s attempt=%d/%d",
                    route,
                    retry_after,
                    is_global,
                    scope,
                    attempt + 1,
                    self.max_retries + 1,
                )

                if attempt < self.max_retries:
                    await self._rate_limiter.handle_rate_limit(
                        route.path,
                        retry_after=retry_after,
                        is_global=is_global,
                        scope=scope,
                    )
                    continue

                raise RateLimited(
                    retry_after=retry_after,
                    is_global=is_global,
                    bucket=resp_headers.get("x-ratelimit-bucket"),
                    scope=scope,
                    status=429,
                    reason="Too Many Requests",
                    method=route.method,
                    url=route.url,
                    response_data=body,
                    headers=resp_headers,
                )

            # ── 5xx Server Error ───────────────────────────────────────────
            if 500 <= status < 600:
                logger.warning("5xx on %s (attempt %d): %d", route, attempt + 1, status)
                if attempt < self.max_retries:
                    await self._rate_limiter.backoff(attempt)
                    continue
                raise exception_from_response(
                    status,
                    response.reason_phrase,
                    method=route.method,
                    url=route.url,
                    response_data=body,
                    headers=dict(response.headers),
                )

            # ── 4xx Client Error — never retry ─────────────────────────────
            raise exception_from_response(
                status,
                response.reason_phrase,
                method=route.method,
                url=route.url,
                response_data=body,
                headers=dict(response.headers),
            )

        # Should never reach here
        raise RuntimeError("Exhausted retries without raising")

    # ─── Convenience Shorthands ──────────────────────────────────────────────

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        **kw: Any,
    ) -> Any:
        """Perform a GET request."""
        return await self.request(Route("GET", path), params=params, **kw)

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kw: Any,
    ) -> Any:
        """Perform a POST request."""
        return await self.request(Route("POST", path), json_payload=json, **kw)

    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kw: Any,
    ) -> Any:
        """Perform a PATCH request."""
        return await self.request(Route("PATCH", path), json_payload=json, **kw)

    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kw: Any,
    ) -> Any:
        """Perform a PUT request."""
        return await self.request(Route("PUT", path), json_payload=json, **kw)

    async def delete(
        self,
        path: str,
        reason: Optional[str] = None,
        **kw: Any,
    ) -> Any:
        """Perform a DELETE request."""
        return await self.request(Route("DELETE", path), reason=reason, **kw)

    # ─── Rate Limiter Passthrough ─────────────────────────────────────────────

    @property
    def rate_limiter(self) -> RateLimiter:
        """Access the underlying ``RateLimiter`` instance."""
        return self._rate_limiter
