"""
exceptions.py — Custom Exception Hierarchy
==========================================

Full exception hierarchy for Dapi. All exceptions trace back to
``DapiException``, enabling broad or specific ``except`` clauses.

Hierarchy:
    DapiException
    ├── ConfigurationError
    ├── InvalidToken
    ├── InvalidArgument
    ├── LoginFailure
    ├── MaxConcurrencyReached
    ├── ResponseCorrupt
    └── DiscordException
        ├── HTTPException (status code based)
        │   ├── BadRequest         (400)
        │   ├── Unauthorized       (401)
        │   ├── Forbidden          (403)
        │   ├── NotFound           (404)
        │   ├── MethodNotAllowed   (405)
        │   ├── Conflict           (409)
        │   ├── RateLimited        (429)
        │   └── ServerError        (5xx)
        └── GatewayException
            └── ConnectionClosed
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


__all__: list[str] = [
    "DapiException",
    "ConfigurationError",
    "InvalidToken",
    "InvalidArgument",
    "LoginFailure",
    "MaxConcurrencyReached",
    "ResponseCorrupt",
    "DiscordException",
    "HTTPException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "Conflict",
    "RateLimited",
    "ServerError",
    "GatewayException",
    "ConnectionClosed",
]


# ═══════════════════════════════════════════════════════════════════════════
#   Base
# ═══════════════════════════════════════════════════════════════════════════

class DapiException(Exception):
    """Base exception for all Dapi errors.

    All exceptions raised by this library inherit from here, so you can
    catch everything with ``except DapiException``.

    Attributes:
        message (str): Human-readable error description.
    """

    def __init__(self, message: str = "An error occurred in Dapi") -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.message!r}>"


class ConfigurationError(DapiException):
    """Raised when the client is misconfigured.

    Example:
        >>> raise ConfigurationError("proxy must be a valid URL")
    """

    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(f"ConfigurationError: {message}")


class InvalidToken(DapiException):
    """Raised when the supplied token has an invalid format.

    Note:
        This is a *format* validation error, not an authentication error.
        An invalid token that passes format validation will raise
        ``Unauthorized`` (401) on the first API call.
    """

    def __init__(self, message: str = "Token format is invalid") -> None:
        super().__init__(f"InvalidToken: {message}")


class InvalidArgument(DapiException):
    """Raised when a function receives an invalid argument value.

    Attributes:
        argument (str): Name of the invalid argument.
    """

    def __init__(self, argument: str, message: str = "Invalid value") -> None:
        self.argument = argument
        super().__init__(f"InvalidArgument '{argument}': {message}")


class LoginFailure(DapiException):
    """Raised when ``client.login()`` cannot authenticate successfully."""

    def __init__(self, message: str = "Login failed") -> None:
        super().__init__(f"LoginFailure: {message}")


class MaxConcurrencyReached(DapiException):
    """Raised when a command exceeds its concurrency limit.

    Attributes:
        name (str): Command or resource name.
        limit (int): Maximum concurrency allowed.
    """

    def __init__(self, name: str, limit: int) -> None:
        self.name = name
        self.limit = limit
        super().__init__(f"MaxConcurrency for '{name}': limit of {limit} reached")


class ResponseCorrupt(DapiException):
    """Raised when Discord returns malformed or unexpected response data."""

    def __init__(self, message: str = "Response data is corrupt or malformed") -> None:
        super().__init__(message)


# ═══════════════════════════════════════════════════════════════════════════
#   Discord API Errors
# ═══════════════════════════════════════════════════════════════════════════

class DiscordException(DapiException):
    """Base for all Discord API errors.

    Attributes:
        code (int | None): Discord JSON error code (e.g. 50013 = Missing Permissions).
        data (dict): Raw response JSON body (may be empty).
    """

    def __init__(
        self,
        message: str = "A Discord API error occurred",
        code: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.data = data or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.code:
            return f"[Code {self.code}] {self.message}"
        return self.message


# ─── HTTP Exceptions ─────────────────────────────────────────────────────────

class HTTPException(DiscordException):
    """Raised for non-success HTTP responses from Discord.

    Attributes:
        status (int): HTTP status code.
        reason (str): HTTP reason phrase.
        method (str): HTTP method used.
        url (str): Endpoint URL.
        response_data (Any): Parsed response body.
        headers (dict): Response headers.
        discord_code (int | None): Discord JSON error code from body.
        error_message (str): Human-readable error from body.
    """

    def __init__(
        self,
        status: int,
        reason: str = "",
        message: str = "",
        method: str = "",
        url: str = "",
        response_data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status = status
        self.reason = reason
        self.method = method
        self.url = url
        self.response_data: Any = response_data
        self.headers: Dict[str, str] = headers or {}

        # Extract Discord-specific error info
        discord_code: Optional[int] = None
        error_msg = message or reason

        if isinstance(response_data, dict):
            discord_code = response_data.get("code")
            if "message" in response_data:
                error_msg = response_data["message"]
            elif "errors" in response_data:
                extracted = self._extract_errors(response_data["errors"])
                if extracted:
                    error_msg = "; ".join(extracted)

        self.discord_code = discord_code
        self.error_message = error_msg

        super().__init__(
            message=f"HTTP {status} {reason}: {error_msg}",
            code=discord_code,
            data=response_data if isinstance(response_data, dict) else {},
        )

    def _extract_errors(
        self,
        errors: Any,
        prefix: str = "",
    ) -> List[str]:
        """Recursively flatten Discord's nested errors dict."""
        messages: List[str] = []
        if not isinstance(errors, dict):
            return messages

        for key, value in errors.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                if "_errors" in value:
                    for err in value["_errors"]:
                        msg = err.get("message", str(err))
                        messages.append(f"{path}: {msg}")
                else:
                    messages.extend(self._extract_errors(value, path))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    messages.extend(self._extract_errors(item, f"{path}[{i}]"))

        return messages

    def __str__(self) -> str:
        if self.discord_code:
            return (
                f"HTTP {self.status} (Discord code {self.discord_code}) "
                f"[{self.method} {self.url}]: {self.error_message}"
            )
        return f"HTTP {self.status} {self.reason} [{self.method} {self.url}]: {self.error_message}"

    def __repr__(self) -> str:
        return (
            f"<HTTPException status={self.status} discord_code={self.discord_code} "
            f"method={self.method!r} url={self.url!r}>"
        )


class BadRequest(HTTPException):
    """HTTP 400 — The request body is invalid.

    Usually caused by missing required fields or constraint violations.

    Attributes:
        field (str | None): Name of the invalid field (if known).
    """

    def __init__(
        self,
        message: str = "Bad request",
        field: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.field = field
        kwargs.setdefault("status", 400)
        kwargs.setdefault("reason", "Bad Request")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        base = f"BadRequest (400): {self.error_message}"
        return f"{base} [field: {self.field!r}]" if self.field else base


class Unauthorized(HTTPException):
    """HTTP 401 — Invalid or expired token.

    This is the most common error for selfbots with bad tokens.
    """

    def __init__(self, message: str = "Unauthorized — invalid token", **kwargs: Any) -> None:
        kwargs.setdefault("status", 401)
        kwargs.setdefault("reason", "Unauthorized")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        return f"Unauthorized (401): {self.error_message} — Your token may be invalid or expired."


class Forbidden(HTTPException):
    """HTTP 403 — Insufficient permissions.

    Attributes:
        permission (str | None): Missing permission name (if known).
    """

    def __init__(
        self,
        message: str = "Forbidden — insufficient permissions",
        permission: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.permission = permission
        kwargs.setdefault("status", 403)
        kwargs.setdefault("reason", "Forbidden")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        base = f"Forbidden (403): {self.error_message}"
        return f"{base} [missing: {self.permission}]" if self.permission else base


class NotFound(HTTPException):
    """HTTP 404 — Resource does not exist.

    Attributes:
        resource_type (str | None): Type of the missing resource.
    """

    def __init__(
        self,
        message: str = "Not Found",
        resource_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.resource_type = resource_type
        kwargs.setdefault("status", 404)
        kwargs.setdefault("reason", "Not Found")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        rt = f"{self.resource_type} " if self.resource_type else ""
        return f"NotFound (404): {rt}not found — {self.error_message}"


class MethodNotAllowed(HTTPException):
    """HTTP 405 — HTTP method is not allowed for this endpoint.

    Attributes:
        allowed_methods (list[str]): Methods allowed by the server.
    """

    def __init__(
        self,
        message: str = "Method Not Allowed",
        allowed_methods: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        self.allowed_methods = allowed_methods or []
        kwargs.setdefault("status", 405)
        kwargs.setdefault("reason", "Method Not Allowed")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        base = f"MethodNotAllowed (405): {self.error_message}"
        if self.allowed_methods:
            return f"{base} — allowed: {', '.join(self.allowed_methods)}"
        return base


class Conflict(HTTPException):
    """HTTP 409 — State conflict (e.g. already a member, message already pinned)."""

    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        kwargs.setdefault("status", 409)
        kwargs.setdefault("reason", "Conflict")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        return f"Conflict (409): {self.error_message}"


class RateLimited(HTTPException):
    """HTTP 429 — Rate limited by Discord.

    Attributes:
        retry_after (float): Seconds to wait before retrying.
        is_global (bool): True if this is the global rate limit.
        bucket (str | None): Rate limit bucket hash.
        scope (str): Rate limit scope ('user', 'global', 'shared').
    """

    def __init__(
        self,
        retry_after: float = 1.0,
        is_global: bool = False,
        bucket: Optional[str] = None,
        scope: str = "user",
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        self.is_global = is_global
        self.bucket = bucket
        self.scope = scope

        kwargs.setdefault("status", 429)
        kwargs.setdefault("reason", "Too Many Requests")
        kwargs.setdefault(
            "message",
            f"Rate limited ({'global' if is_global else 'bucket'}). "
            f"Retry after {retry_after:.3f}s",
        )
        super().__init__(**kwargs)

    def __str__(self) -> str:
        kind = "Global" if self.is_global else "Bucket"
        return (
            f"RateLimited [{kind}] scope={self.scope!r} "
            f"retry_after={self.retry_after:.3f}s bucket={self.bucket!r}"
        )

    def __repr__(self) -> str:
        return (
            f"<RateLimited retry_after={self.retry_after} "
            f"is_global={self.is_global} bucket={self.bucket!r}>"
        )


class ServerError(HTTPException):
    """HTTP 5xx — Discord internal server error.

    These are transient errors on Discord's side and can usually be retried.
    """

    def __init__(self, message: str = "Discord server error", **kwargs: Any) -> None:
        kwargs.setdefault("status", 500)
        kwargs.setdefault("reason", "Internal Server Error")
        super().__init__(message=message, **kwargs)

    def __str__(self) -> str:
        return f"ServerError ({self.status}): {self.error_message}"


# ─── Gateway Exceptions ───────────────────────────────────────────────────────

class GatewayException(DiscordException):
    """Base exception for WebSocket Gateway errors.

    Attributes:
        gateway_code (int | None): Gateway close code.
        close_reason (str): Close reason string.
    """

    def __init__(
        self,
        message: str = "Gateway error",
        code: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.gateway_code = code
        self.close_reason = message
        super().__init__(message=message, code=code, data=data)

    def __str__(self) -> str:
        if self.gateway_code:
            return f"GatewayException [code {self.gateway_code}]: {self.close_reason}"
        return f"GatewayException: {self.close_reason}"


class ConnectionClosed(GatewayException):
    """Raised when the gateway WebSocket connection closes.

    Attributes:
        can_reconnect (bool): Whether reconnection is possible.
    """

    def __init__(
        self,
        code: Optional[int] = None,
        reason: Optional[str] = None,
        can_reconnect: bool = True,
    ) -> None:
        self.can_reconnect = can_reconnect
        msg = f"Connection closed (code={code}): {reason or 'unknown reason'}"
        super().__init__(message=msg, code=code)

    def __str__(self) -> str:
        reconnect = "reconnectable" if self.can_reconnect else "non-reconnectable"
        return f"ConnectionClosed [{reconnect}] code={self.gateway_code}: {self.close_reason}"


# ─── HTTP Status → Exception Mapping ─────────────────────────────────────────

_STATUS_MAP: Dict[int, type] = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    405: MethodNotAllowed,
    409: Conflict,
    429: RateLimited,
}


def exception_from_response(
    status: int,
    reason: str = "",
    message: str = "",
    method: str = "",
    url: str = "",
    response_data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPException:
    """Factory: create the appropriate HTTPException subclass for a status code.

    Args:
        status: HTTP status code.
        reason: HTTP reason phrase.
        message: Error message.
        method: HTTP method.
        url: Request URL.
        response_data: Parsed response body.
        headers: Response headers.

    Returns:
        Appropriate HTTPException subclass instance.
    """
    klass: type
    if status in _STATUS_MAP:
        klass = _STATUS_MAP[status]
    elif 500 <= status < 600:
        klass = ServerError
    else:
        klass = HTTPException

    return klass(
        message=message,
        status=status,
        reason=reason,
        method=method,
        url=url,
        response_data=response_data,
        headers=headers,
    )
