"""
disapi/client.py — Main Discord Client (Async & Sync) — ELITE v4.0
==================================================================

Production-grade async-first client with advanced event system, 
connection pooling, health checks, and comprehensive lifecycle management.

Features:
  - Event-driven architecture (ready, message, presence_update, etc)
  - Advanced connection pooling & session caching
  - Health checks with auto-reconnect & adaptive backoff
  - Structured logging with debug modes
  - Full async/sync support with SyncClient wrapper
  - Context manager support for resource management
  - Built-in rate limit handling

Warning:
  Self-bot usage violates Discord ToS. Use at your own risk.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from .http_client import HTTPClient
from .rate_limiter import RateLimiter
from .gateway import Gateway, GatewayConfig, EventType
from .api.messages import MessagesAPI
from .api.users import UsersAPI
from .api.guilds import GuildsAPI
from .api.channels import ChannelsAPI
from .api.reactions import ReactionsAPI
from .api.relationships import RelationshipsAPI
from .api.presence import PresenceAPI
from .api.misc import MiscAPI
from .models.user import User
from .models.message import Message
from .models.guild import Guild
from .models.channel import Channel
from .exceptions import (
    DisapiException,
    InvalidToken,
    LoginFailure,
    ConnectionClosed,
)
from .constants import DEFAULT_REQUEST_TIMEOUT, DEFAULT_RATE_LIMIT_RETRIES
from .utils import validate_token, setup_logging

__all__ = ["Client", "SyncClient", "ClientOptions"]

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ClientOptions:
    """Advanced client configuration options.
    
    Attributes:
        proxy: HTTP proxy URL (e.g., 'http://127.0.0.1:8080').
        timeout: Request timeout in seconds (default: 30).
        max_retries: Max retry attempts for rate limits/5xx (default: 5).
        debug: Enable debug logging (default: False).
        log_level: Logging level (default: INFO).
        suppress_warnings: Suppress ToS warning on import (default: False).
        enable_gateway: Enable WebSocket gateway (default: True).
        gateway_intents: Intents bitmask (default: 33281).
        auto_reconnect: Auto-reconnect on disconnect (default: True).
        heartbeat_interval: Heartbeat interval in ms (0 = auto).
        health_check_interval: Health check interval in seconds (default: 30).
        max_reconnect_backoff: Max backoff for exponential retry (default: 120s).
        session_cache_size: Max cached session info (default: 100).
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        debug: bool = False,
        log_level: int = logging.INFO,
        suppress_warnings: bool = False,
        enable_gateway: bool = True,
        gateway_intents: int = 33281,
        auto_reconnect: bool = True,
        heartbeat_interval: int = 0,
        health_check_interval: int = 30,
        max_reconnect_backoff: int = 120,
        session_cache_size: int = 100,
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug
        self.log_level = log_level
        self.suppress_warnings = suppress_warnings
        self.enable_gateway = enable_gateway
        self.gateway_intents = gateway_intents
        self.auto_reconnect = auto_reconnect
        self.heartbeat_interval = heartbeat_interval
        self.health_check_interval = health_check_interval
        self.max_reconnect_backoff = max_reconnect_backoff
        self.session_cache_size = session_cache_size


class Client:
    """Advanced async Discord User API Client with event system.
    
    Production-grade client with advanced features:
      - Event-driven architecture (ready, message, presence, etc.)
      - Connection pooling & session caching
      - Health checks with adaptive backoff
      - Automatic reconnection
      - Structured logging
    
    Example:
        async with Client("token") as client:
            @client.event(EventType.READY)
            async def on_ready(data):
                print(f"Ready as {data['user']['username']}")
            
            @client.event(EventType.MESSAGE_CREATE)
            async def on_message(data):
                print(data["content"])
            
            await client.login()
            await client.gateway.connect()
    """

    def __init__(self, token: str, options: Optional[ClientOptions] = None) -> None:
        """Initialize client.
        
        Args:
            token: Discord user token.
            options: ClientOptions for configuration.
            
        Raises:
            InvalidToken: If token format is invalid.
        """
        if not token or not isinstance(token, str):
            raise InvalidToken("Token must be a non-empty string")
        
        self._token = token
        self._options = options or ClientOptions()
        self._closed = True
        self.user: Optional[User] = None
        
        # Session tracking
        self._session_id: Optional[str] = None
        self._resume_url: Optional[str] = None
        self._session_cache: Dict[str, Any] = {}
        self._last_heartbeat: float = 0.0
        self._last_ack: float = 0.0
        self._latency: float = 0.0
        
        # Connection state
        self._connecting = False
        self._reconnect_backoff = 1.0
        self._health_check_task: Optional[asyncio.Task[None]] = None
        self._reconnect_count = 0
        self._last_connection_time = 0.0
        
        # Event system
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._event_lock = asyncio.Lock()
        
        # Initialize HTTP
        self._rate_limiter = RateLimiter()
        self._http = HTTPClient(
            token=token,
            proxy=self._options.proxy,
            timeout=self._options.timeout,
            max_retries=self._options.max_retries,
            debug=self._options.debug,
            rate_limiter=self._rate_limiter,
        )
        
        # Initialize Gateway
        self._gateway: Optional[Gateway] = None
        if self._options.enable_gateway:
            gateway_config = GatewayConfig(
                token=token,
                intents=self._options.gateway_intents,
                compress=True,
            )
            self._gateway = Gateway(
                token=token,
                config=gateway_config,
                auto_reconnect=self._options.auto_reconnect,
            )
        
        # Initialize API modules
        self.messages = MessagesAPI(self._http)
        self.users = UsersAPI(self._http)
        self.guilds = GuildsAPI(self._http)
        self.channels = ChannelsAPI(self._http)
        self.reactions = ReactionsAPI(self._http)
        self.relationships = RelationshipsAPI(self._http)
        self.presence = PresenceAPI(self._http)
        self.misc = MiscAPI(self._http)
        
        setup_logging(self._options.log_level, self._options.debug)
        logger.debug(f"Client initialized (gateway={'enabled' if self._gateway else 'disabled'})")

    async def __aenter__(self) -> Client:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize client (create HTTP session)."""
        if not self._closed:
            logger.warning("Client already connected")
            return
        
        if self._connecting:
            logger.warning("Connection in progress...")
            return
        
        try:
            self._connecting = True
            await self._http.connect()
            self._closed = False
            self._last_connection_time = time.time()
            self._reconnect_count = 0
            self._reconnect_backoff = 1.0
            
            # Start health check
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("Client connected successfully")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            await self.close()
            raise
        finally:
            self._connecting = False

    async def close(self) -> None:
        """Close client and all connections."""
        if self._closed and not self._health_check_task:
            return
        
        logger.info("Closing client...")
        try:
            # Cancel health check
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close gateway
            if self._gateway:
                try:
                    await self._gateway.close()
                except Exception as e:
                    logger.debug(f"Error closing gateway: {e}")
            
            # Close HTTP
            await self._http.close()
        except Exception as e:
            logger.error(f"Error during close: {e}")
        finally:
            self._closed = True
            self._health_check_task = None
            logger.info("Client closed")

    async def login(self) -> User:
        """Login and get current user.
        
        Returns:
            Current User object.
            
        Raises:
            InvalidToken: If token is invalid.
            LoginFailure: If login fails.
        """
        if self._closed:
            raise DisapiException("Client not connected. Call .connect() first.")
        
        try:
            logger.debug("Authenticating...")
            user_data = await self._http.request("GET", "/users/@me")
            self.user = User(user_data)
            logger.info(f"Logged in as {self.user['username']}#{self.user['discriminator']}")
            
            # Dispatch login event
            await self._dispatch_event("LOGIN", {"user": user_data})
            
            return self.user
        except Exception as e:
            if "401" in str(e):
                raise InvalidToken("Invalid token") from e
            raise LoginFailure(f"Login failed: {e}") from e

    async def _health_check_loop(self) -> None:
        """Background health check task."""
        while not self._closed:
            try:
                await asyncio.sleep(self._options.health_check_interval)
                
                if self._closed:
                    break
                
                # Check if HTTP is healthy
                try:
                    await self._http.request("GET", "/users/@me", timeout=5.0)
                    self._reconnect_backoff = 1.0
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
                    
                    if not self._closed and self._options.auto_reconnect:
                        await self._handle_reconnect()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in health check: {e}")

    async def _handle_reconnect(self) -> None:
        """Handle automatic reconnection with adaptive backoff."""
        self._reconnect_count += 1
        backoff = min(
            self._reconnect_backoff * (2 ** (self._reconnect_count - 1)),
            self._options.max_reconnect_backoff
        )
        
        logger.warning(
            f"Reconnecting (attempt {self._reconnect_count}, "
            f"backoff={backoff:.1f}s)..."
        )
        
        try:
            await asyncio.sleep(backoff)
            await self.close()
            await self.connect()
            await self.login()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

    def event(self, event_type: str) -> Callable:
        """Register event listener (decorator).
        
        Args:
            event_type: Event type (e.g., EventType.MESSAGE_CREATE)
            
        Returns:
            Decorator function.
        
        Example:
            @client.event(EventType.MESSAGE_CREATE)
            async def on_message(data):
                print(data['content'])
        """
        def decorator(func: Callable) -> Callable:
            self.on(event_type)(func)
            return func
        return decorator

    def on(self, event_type: str) -> Callable:
        """Register event listener.
        
        Args:
            event_type: Event type.
            
        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            logger.debug(f"Registered handler for {event_type}: {func.__name__}")
            return func
        return decorator

    async def _dispatch_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Dispatch event to all registered handlers.
        
        Args:
            event_type: Event type.
            data: Event data.
        """
        if event_type not in self._event_handlers:
            return
        
        handlers = self._event_handlers[event_type]
        tasks = []
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in {event_type} handler {handler.__name__}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_current_user(self) -> User:
        """Get current user.
        
        Returns:
            Current User object.
        """
        if not self.user:
            return await self.login()
        return self.user

    async def get_user(self, user_id: str) -> User:
        """Get user by ID.
        
        Args:
            user_id: User ID.
            
        Returns:
            User object.
        """
        data = await self._http.request("GET", f"/users/{user_id}")
        return User(data)

    async def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID.
        
        Args:
            channel_id: Channel ID.
            
        Returns:
            Channel object.
        """
        data = await self._http.request("GET", f"/channels/{channel_id}")
        return Channel(data)

    async def get_guild(self, guild_id: str) -> Guild:
        """Get guild by ID.
        
        Args:
            guild_id: Guild ID.
            
        Returns:
            Guild object.
        """
        data = await self._http.request("GET", f"/guilds/{guild_id}")
        return Guild(data)

    async def get_message(self, channel_id: str, message_id: str) -> Message:
        """Get message by ID.
        
        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            
        Returns:
            Message object.
        """
        data = await self._http.request(
            "GET", 
            f"/channels/{channel_id}/messages/{message_id}"
        )
        return Message(data)

    @property
    def gateway(self) -> Optional[Gateway]:
        """Get gateway (if enabled)."""
        return self._gateway

    @property
    def http(self) -> HTTPClient:
        """Get HTTP client."""
        return self._http

    @property
    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._closed

    @property
    def latency(self) -> float:
        """Get estimated latency in seconds."""
        return self._latency



class SyncClient:
    """Synchronous wrapper around async Client.
    
    Provides blocking interface for users who prefer sync code.
    All methods are blocking and run in an event loop.
    
    Example:
        with SyncClient("token") as client:
            user = client.login()
            msg = client.messages.send("channel_id", "Hello!")
    """

    def __init__(self, token: str, options: Optional[ClientOptions] = None) -> None:
        """Initialize sync client."""
        if options:
            options.enable_gateway = False
        else:
            options = ClientOptions(enable_gateway=False)
        
        self._client = Client(token, options)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def __enter__(self) -> SyncClient:
        """Context manager entry."""
        self._run_sync(self._client.connect())
        self._run_sync(self._client.login())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        try:
            self._run_sync(self._client.close())
        except Exception as e:
            logger.error(f"Error closing SyncClient: {e}")

    def __repr__(self) -> str:
        return f"<SyncClient user={self._client.user}>"

    def _run_sync(self, coro: Awaitable[T]) -> T:
        """Run async code synchronously.
        
        Args:
            coro: Coroutine to run.
            
        Returns:
            Result from coroutine.
        """
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "Cannot use SyncClient from async context. "
                "Use Client directly with async/await."
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def login(self) -> User:
        """Login and authenticate.
        
        Returns:
            Current User object.
        """
        return self._run_sync(self._client.login())

    def close(self) -> None:
        """Close client."""
        self._run_sync(self._client.close())

    def get_current_user(self) -> User:
        """Get current user.
        
        Returns:
            Current User object.
        """
        return self._run_sync(self._client.get_current_user())

    def get_user(self, user_id: str) -> User:
        """Get user by ID.
        
        Args:
            user_id: User ID.
            
        Returns:
            User object.
        """
        return self._run_sync(self._client.get_user(user_id))

    def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID.
        
        Args:
            channel_id: Channel ID.
            
        Returns:
            Channel object.
        """
        return self._run_sync(self._client.get_channel(channel_id))

    def get_guild(self, guild_id: str) -> Guild:
        """Get guild by ID.
        
        Args:
            guild_id: Guild ID.
            
        Returns:
            Guild object.
        """
        return self._run_sync(self._client.get_guild(guild_id))

    def get_message(self, channel_id: str, message_id: str) -> Message:
        """Get message by ID.
        
        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            
        Returns:
            Message object.
        """
        return self._run_sync(self._client.get_message(channel_id, message_id))

    @property
    def user(self) -> Optional[User]:
        """Get current user."""
        return self._client.user

    @property
    def messages(self) -> MessagesAPI:
        """Access messages API."""
        return self._client.messages

    @property
    def users(self) -> UsersAPI:
        """Access users API."""
        return self._client.users

    @property
    def guilds(self) -> GuildsAPI:
        """Access guilds API."""
        return self._client.guilds

    @property
    def channels(self) -> ChannelsAPI:
        """Access channels API."""
        return self._client.channels

    @property
    def reactions(self) -> ReactionsAPI:
        """Access reactions API."""
        return self._client.reactions

    @property
    def relationships(self) -> RelationshipsAPI:
        """Access relationships API."""
        return self._client.relationships

    @property
    def presence(self) -> PresenceAPI:
        """Access presence API."""
        return self._client.presence

    @property
    def misc(self) -> MiscAPI:
        """Access misc API."""
        return self._client.misc

    @property
    def http(self) -> HTTPClient:
        """Get HTTP client."""
        return self._client.http

    @property
    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._client.is_closed

