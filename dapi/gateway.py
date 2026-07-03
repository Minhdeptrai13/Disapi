
gateway.py — Discord Gateway WebSocket Handler (ELITE v4.0)


Production-grade Gateway client with client integration.


from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

try:
    import websockets
    import websockets.legacy.client as ws_legacy
    from websockets.exceptions import ConnectionClosed as WSConnectionClosed
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    ws_legacy = None
    WSConnectionClosed = Exception

from .constants import (
    ActivityType,
    GatewayCloseCode,
    GatewayOpcode,
    Status,
    get_gateway_properties,
    CLIENT_BUILD_NUMBER,
    GATEWAY_URL,
)
from .exceptions import ConnectionClosed, GatewayException

__all__ = ["Gateway", "GatewayConfig", "EventType"]
<<<<<<< HEAD:disapi/gateway.py

logger = logging.getLogger("disapi.gateway")

=======

logger = logging.getLogger("dapi.gateway")

>>>>>>> c43f783 (upd):dapi/gateway.py
EventCallback = Union[
    Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    Callable[[Dict[str, Any]], None],
]


class EventType:
    READY                        = "READY"
    RESUMED                      = "RESUMED"
    APPLICATION_COMMAND_PERMISSIONS_UPDATE = "APPLICATION_COMMAND_PERMISSIONS_UPDATE"
    AUTO_MODERATION_RULE_CREATE  = "AUTO_MODERATION_RULE_CREATE"
    AUTO_MODERATION_RULE_UPDATE  = "AUTO_MODERATION_RULE_UPDATE"
    AUTO_MODERATION_RULE_DELETE  = "AUTO_MODERATION_RULE_DELETE"
    AUTO_MODERATION_ACTION_EXECUTION = "AUTO_MODERATION_ACTION_EXECUTION"
    CHANNEL_CREATE               = "CHANNEL_CREATE"
    CHANNEL_UPDATE               = "CHANNEL_UPDATE"
    CHANNEL_DELETE               = "CHANNEL_DELETE"
    CHANNEL_PINS_UPDATE          = "CHANNEL_PINS_UPDATE"
    THREAD_CREATE                = "THREAD_CREATE"
    THREAD_UPDATE                = "THREAD_UPDATE"
    THREAD_DELETE                = "THREAD_DELETE"
    THREAD_LIST_SYNC             = "THREAD_LIST_SYNC"
    THREAD_MEMBER_UPDATE         = "THREAD_MEMBER_UPDATE"
    THREAD_MEMBERS_UPDATE        = "THREAD_MEMBERS_UPDATE"
    GUILD_CREATE                 = "GUILD_CREATE"
    GUILD_UPDATE                 = "GUILD_UPDATE"
    GUILD_DELETE                 = "GUILD_DELETE"
    GUILD_AUDIT_LOG_ENTRY_CREATE = "GUILD_AUDIT_LOG_ENTRY_CREATE"
    GUILD_BAN_ADD                = "GUILD_BAN_ADD"
    GUILD_BAN_REMOVE             = "GUILD_BAN_REMOVE"
    GUILD_EMOJIS_UPDATE          = "GUILD_EMOJIS_UPDATE"
    GUILD_STICKERS_UPDATE        = "GUILD_STICKERS_UPDATE"
    GUILD_INTEGRATIONS_UPDATE    = "GUILD_INTEGRATIONS_UPDATE"
    GUILD_MEMBER_ADD             = "GUILD_MEMBER_ADD"
    GUILD_MEMBER_REMOVE          = "GUILD_MEMBER_REMOVE"
    GUILD_MEMBER_UPDATE          = "GUILD_MEMBER_UPDATE"
    GUILD_MEMBERS_CHUNK          = "GUILD_MEMBERS_CHUNK"
    GUILD_ROLE_CREATE            = "GUILD_ROLE_CREATE"
    GUILD_ROLE_UPDATE            = "GUILD_ROLE_UPDATE"
    GUILD_ROLE_DELETE            = "GUILD_ROLE_DELETE"
    GUILD_SCHEDULED_EVENT_CREATE = "GUILD_SCHEDULED_EVENT_CREATE"
    GUILD_SCHEDULED_EVENT_UPDATE = "GUILD_SCHEDULED_EVENT_UPDATE"
    GUILD_SCHEDULED_EVENT_DELETE = "GUILD_SCHEDULED_EVENT_DELETE"
    GUILD_SCHEDULED_EVENT_USER_ADD    = "GUILD_SCHEDULED_EVENT_USER_ADD"
    GUILD_SCHEDULED_EVENT_USER_REMOVE = "GUILD_SCHEDULED_EVENT_USER_REMOVE"
    INTEGRATION_CREATE           = "INTEGRATION_CREATE"
    INTEGRATION_UPDATE           = "INTEGRATION_UPDATE"
    INTEGRATION_DELETE           = "INTEGRATION_DELETE"
    INTERACTION_CREATE           = "INTERACTION_CREATE"
    INVITE_CREATE                = "INVITE_CREATE"
    INVITE_DELETE                = "INVITE_DELETE"
    MESSAGE_CREATE               = "MESSAGE_CREATE"
    MESSAGE_UPDATE               = "MESSAGE_UPDATE"
    MESSAGE_DELETE               = "MESSAGE_DELETE"
    MESSAGE_DELETE_BULK          = "MESSAGE_DELETE_BULK"
    MESSAGE_REACTION_ADD         = "MESSAGE_REACTION_ADD"
    MESSAGE_REACTION_REMOVE      = "MESSAGE_REACTION_REMOVE"
    MESSAGE_REACTION_REMOVE_ALL  = "MESSAGE_REACTION_REMOVE_ALL"
    MESSAGE_REACTION_REMOVE_EMOJI = "MESSAGE_REACTION_REMOVE_EMOJI"
    PRESENCE_UPDATE              = "PRESENCE_UPDATE"
    TYPING_START                 = "TYPING_START"
    USER_UPDATE                  = "USER_UPDATE"
    VOICE_STATE_UPDATE           = "VOICE_STATE_UPDATE"
    VOICE_SERVER_UPDATE          = "VOICE_SERVER_UPDATE"
    WEBHOOKS_UPDATE              = "WEBHOOKS_UPDATE"
    RELATIONSHIP_ADD             = "RELATIONSHIP_ADD"
    RELATIONSHIP_REMOVE          = "RELATIONSHIP_REMOVE"
    READY_SUPPLEMENTAL           = "READY_SUPPLEMENTAL"
    SESSIONS_REPLACE             = "SESSIONS_REPLACE"


@dataclass
class GatewayConfig:
    token: str
    intents: int = 0
    large_threshold: int = 250
    capabilities: int = 16381
    compress: bool = True
    properties: Dict[str, Any] = field(default_factory=get_gateway_properties)
    initial_presence: Optional[Dict[str, Any]] = None


class Gateway:
    def __init__(
        self,
        token: str,
        config: Optional[GatewayConfig] = None,
        auto_reconnect: bool = True,
        client: Optional[Any] = None,          # <--- THÊM client
    ) -> None:
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "The 'websockets' package is required for Gateway support. "
                "Install it with: pip install dapi[gateway]"
            )

        self.token = token
        self.config = config or GatewayConfig(token=token)
        self.auto_reconnect = auto_reconnect
        self.client = client                    # <--- LƯU LẠI

        self._ws: Optional[Any] = None
        self._connected: bool = False
        self._session_id: Optional[str] = None
        self._sequence: Optional[int] = None
        self._resume_url: Optional[str] = None
        self._heartbeat_interval: float = 41.25
        self._last_heartbeat_sent: float = 0.0
        self._last_heartbeat_ack: float = 0.0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

        self._reconnect_delay: float = 1.0
        self._reconnect_count: int = 0
        self._max_reconnect_delay: float = 120.0
        self._last_reconnect_time: float = 0.0
        self._connection_start_time: float = 0.0

        self._heartbeat_acks_missed: int = 0
        self._max_missed_acks: int = 3
        self._last_latency: float = 0.0
        self._latency_history: List[float] = []
        self._max_history_size: int = 10

        self._zlib_decompressor = zlib.decompressobj()
        self._buffer = bytearray()
        self._ZLIB_SUFFIX = b"\x00\x00\xff\xff"
        self._decompress_lock = asyncio.Lock()

        self._listeners: Dict[str, List[EventCallback]] = {}
        self._once_listeners: Dict[str, List[EventCallback]] = {}
        self._listener_lock = asyncio.Lock()
        self._event_queue: asyncio.Queue[tuple[str, Dict]] = asyncio.Queue(maxsize=1000)
        self._event_dispatcher_task: Optional[asyncio.Task] = None

        self._ready: bool = False
        self._user: Optional[Dict[str, Any]] = None
        self._guilds_loaded: int = 0

    # ─── Properties ──────────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def sequence(self) -> Optional[int]:
        return self._sequence

    @property
    def latency(self) -> float:
        if self._last_heartbeat_ack and self._last_heartbeat_sent:
            return max(0.0, self._last_heartbeat_ack - self._last_heartbeat_sent)
        return 0.0

    @property
    def avg_latency(self) -> float:
        if not self._latency_history:
            return 0.0
        return sum(self._latency_history) / len(self._latency_history)

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        return self._user

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    @property
    def heartbeat_acks_missed(self) -> int:
        return self._heartbeat_acks_missed

    @property
    def connection_uptime(self) -> float:
        if not self._connected:
            return 0.0
        return time.monotonic() - self._connection_start_time

    # ─── Event Registration ──────────────────────────────────────────────────

    def on(self, event: str) -> Callable[[EventCallback], EventCallback]:
        def decorator(func: EventCallback) -> EventCallback:
            key = event.upper()
            self._listeners.setdefault(key, []).append(func)
            return func
        return decorator

    def once(self, event: str) -> Callable[[EventCallback], EventCallback]:
        def decorator(func: EventCallback) -> EventCallback:
            key = event.upper()
            self._once_listeners.setdefault(key, []).append(func)
            return func
        return decorator

    def add_listener(self, event: str, callback: EventCallback) -> None:
        self._listeners.setdefault(event.upper(), []).append(callback)

    def remove_listener(self, event: str, callback: EventCallback) -> None:
        key = event.upper()
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass

    # ─── Connection ───────────────────────────────────────────────────────────

    async def connect(self, url: Optional[str] = None) -> None:
        gateway_url = url or self._resume_url or GATEWAY_URL
        self._reconnect_delay = 1.0
        self._reconnect_count = 0

        while True:
            try:
                await self._run_connection(gateway_url)
            except ConnectionClosed as exc:
                if not exc.can_reconnect or not self.auto_reconnect:
                    raise
                gateway_url = self._resume_url or GATEWAY_URL
            except Exception as exc:
                logger.error("Unexpected gateway error: %s", exc, exc_info=True)
                if not self.auto_reconnect:
                    raise
            else:
                if not self.auto_reconnect:
                    break

            self._reconnect_count += 1
            jitter = random.uniform(0, 0.1 * self._reconnect_delay)
            delay = min(
                self._reconnect_delay * (2 ** (self._reconnect_count - 1)),
                self._max_reconnect_delay
            ) + jitter
            logger.info("Reconnecting in %.2fs (attempt %d)…", delay, self._reconnect_count)
            await asyncio.sleep(delay)

    async def _run_connection(self, url: str) -> None:
        logger.info("Connecting to gateway: %s", url)
        extra_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Origin": "https://discord.com",
        }
        try:
            async with websockets.connect(
                url,
                max_size=None,
                ping_interval=None,
                close_timeout=10,
                additional_headers=extra_headers,
            ) as ws:
                self._ws = ws
                self._connected = True
                self._connection_start_time = time.monotonic()
                self._heartbeat_acks_missed = 0
                self._latency_history.clear()
                self._zlib_decompressor = zlib.decompressobj()
                self._buffer = bytearray()
                logger.info("Gateway WebSocket connected")

                self._event_dispatcher_task = asyncio.create_task(self._event_dispatch_loop())

                try:
                    async for message in ws:
                        await self._handle_raw(message)
                except WSConnectionClosed as exc:
                    code = getattr(exc, "code", 1000)
                    reason = getattr(exc, "reason", "")
                    await self._handle_close(code, reason)
                finally:
                    self._connected = False
                    await self._cancel_tasks()
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise

    # ─── Message Handling ─────────────────────────────────────────────────────

    async def _handle_raw(self, raw: Union[str, bytes]) -> None:
        if isinstance(raw, bytes):
            self._buffer.extend(raw)
            if len(raw) >= 4 and raw[-4:] == self._ZLIB_SUFFIX:
                try:
                    async with self._decompress_lock:
                        data = self._zlib_decompressor.decompress(self._buffer)
                    self._buffer = bytearray()
                    await self._handle_json(data.decode("utf-8"))
                except zlib.error as exc:
                    logger.warning("zlib decompression failed: %s", exc)
                    self._buffer = bytearray()
                except Exception as exc:
                    logger.error(f"Error decompressing: {exc}")
                    self._buffer = bytearray()
        else:
            await self._handle_json(raw)

    async def _handle_json(self, text: str) -> None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse gateway JSON: %s", exc)
            return

        op: int = payload.get("op", -1)
        d: Any = payload.get("d")
        s: Optional[int] = payload.get("s")
        t: Optional[str] = payload.get("t")

        if s is not None:
            self._sequence = s

        await self._dispatch_opcode(op, d, t)

    async def _dispatch_opcode(self, op: int, data: Any, event_name: Optional[str]) -> None:
        if op == GatewayOpcode.HELLO:
            await self._on_hello(data)
        elif op == GatewayOpcode.DISPATCH:
            await self._on_dispatch(event_name, data)
        elif op == GatewayOpcode.HEARTBEAT:
            await self._send_heartbeat()
        elif op == GatewayOpcode.HEARTBEAT_ACK:
            self._last_heartbeat_ack = time.monotonic()
            latency = self.latency
            self._last_latency = latency
            self._latency_history.append(latency)
            if len(self._latency_history) > self._max_history_size:
                self._latency_history.pop(0)
            self._heartbeat_acks_missed = 0
            logger.debug("Heartbeat ACK (lat=%.1fms, avg=%.1fms)", latency * 1000, self.avg_latency * 1000)
        elif op == GatewayOpcode.RECONNECT:
            logger.info("Server requested RECONNECT")
            await self._ws.close(1000)
        elif op == GatewayOpcode.INVALID_SESSION:
            resumable = bool(data)
            logger.warning("Invalid session — resumable=%s", resumable)
            if not resumable:
                self._session_id = None
                self._sequence = None
            await asyncio.sleep(random.uniform(1.0, 5.0))
            if resumable:
                await self._send_resume()
            else:
                await self._send_identify()
        else:
            logger.debug("Unhandled opcode: %d", op)

    async def _on_hello(self, data: Dict[str, Any]) -> None:
        interval_ms: int = data.get("heartbeat_interval", 41250)
        self._heartbeat_interval = interval_ms / 1000.0
        logger.debug("Hello: heartbeat_interval=%.3fs", self._heartbeat_interval)

        self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())

        if self._session_id and self._sequence is not None:
            await self._send_resume()
        else:
            await self._send_identify()

    async def _on_dispatch(self, event: Optional[str], data: Any) -> None:
        if event is None:
            return

        if event == EventType.READY:
            self._session_id = data.get("session_id")
            self._resume_url = data.get("resume_gateway_url")
            self._user = data.get("user")
            self._ready = True
            self._reconnect_count = 0
            logger.info("READY — session=%s user=%s", self._session_id, self._user.get("username") if self._user else "?")
        elif event == EventType.RESUMED:
            logger.info("Gateway session RESUMED (uptime=%.1fs)", self.connection_uptime)
        elif event == EventType.GUILD_CREATE:
            self._guilds_loaded += 1
            logger.debug("Guild created (total=%d)", self._guilds_loaded)

        try:
            self._event_queue.put_nowait((event, data))
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping %s event", event)

    async def _handle_close(self, code: int, reason: str) -> None:
        self._connected = False
        logger.warning("Gateway closed: code=%d reason=%r", code, reason)
        can_reconnect = code not in GatewayCloseCode.FATAL_CODES
        if not can_reconnect:
            raise ConnectionClosed(code=code, reason=reason, can_reconnect=False)
        if code in (GatewayCloseCode.GOING_AWAY, GatewayCloseCode.UNKNOWN_ERROR, GatewayCloseCode.SESSION_TIMEOUT):
            pass
        elif code == GatewayCloseCode.INVALID_SEQ:
            self._sequence = None

    # ─── Heartbeat ────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        await asyncio.sleep(random.uniform(0, self._heartbeat_interval))
        while self._connected:
            try:
                await self._send_heartbeat()
                if self._heartbeat_acks_missed >= self._max_missed_acks:
                    logger.error("Too many missed ACKs (%d/%d), reconnecting", self._heartbeat_acks_missed, self._max_missed_acks)
                    if self._ws:
                        await self._ws.close(1000)
                    break
                self._heartbeat_acks_missed += 1
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Heartbeat loop error: %s", exc)
                break

    async def _send_heartbeat(self) -> None:
        self._last_heartbeat_sent = time.monotonic()
        await self._send({"op": GatewayOpcode.HEARTBEAT, "d": self._sequence})
        logger.debug("Heartbeat sent (seq=%s)", self._sequence)

    # ─── Sending ─────────────────────────────────────────────────────────────

    async def _send(self, payload: Dict[str, Any]) -> None:
        if self._ws is None:
            raise GatewayException("Not connected to gateway")
        await self._ws.send(json.dumps(payload))

    async def _send_identify(self) -> None:
        presence = self.config.initial_presence or {
            "status": Status.ONLINE,
            "since": 0,
            "activities": [],
            "afk": False,
        }
        payload = {
            "op": GatewayOpcode.IDENTIFY,
            "d": {
                "token": self.token,
                "capabilities": self.config.capabilities,
                "properties": self.config.properties,
                "presence": presence,
                "compress": False,
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1,
                    "private_channels_version": "0",
                    "api_code_version": 0,
                },
            },
        }
        await self._send(payload)
        logger.info("IDENTIFY sent")

    async def _send_resume(self) -> None:
        payload = {
            "op": GatewayOpcode.RESUME,
            "d": {
                "token": self.token,
                "session_id": self._session_id,
                "seq": self._sequence,
            },
        }
        await self._send(payload)
        logger.info("RESUME sent (session=%s seq=%s)", self._session_id, self._sequence)

    # ─── Emit ─────────────────────────────────────────────────────────────────

    async def _event_dispatch_loop(self) -> None:
        while self._connected:
            try:
                event, data = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._emit(event, data)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event dispatcher: {e}")

    async def _emit(self, event: str, data: Any) -> None:
        """Dispatch event to gateway listeners AND forward to client."""
        key = event.upper()

        # 1. Gateway's own listeners
        persistent = list(self._listeners.get(key, []))
        once_cbs = self._once_listeners.pop(key, [])

        tasks = []
        for cb in persistent:
            try:
                if asyncio.iscoroutinefunction(cb):
                    tasks.append(self._safe_call_handler(cb, data, event))
                else:
                    cb(data)
            except Exception as exc:
                logger.error("Error in gateway listener for %s: %s", event, exc)

        for cb in once_cbs:
            try:
                if asyncio.iscoroutinefunction(cb):
                    tasks.append(self._safe_call_handler(cb, data, event))
                else:
                    cb(data)
            except Exception as exc:
                logger.error("Error in gateway once-listener for %s: %s", event, exc)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 2. Forward to Client
        if self.client is not None:
            try:
                await self.client._dispatch_event(event, data)
            except Exception as exc:
                logger.error("Error forwarding event %s to client: %s", event, exc)

    async def _safe_call_handler(self, handler: Callable, data: Any, event: str) -> None:
        try:
            await handler(data)
        except Exception as exc:
            logger.error("Error in %s handler %s: %s", event, getattr(handler, "__name__", "unknown"), exc, exc_info=True)

    # ─── Gateway Commands ─────────────────────────────────────────────────────

    async def update_presence(self, status: str = Status.ONLINE, activities: Optional[List[Dict[str, Any]]] = None, afk: bool = False, since: Optional[int] = None) -> None:
        payload = {
            "op": GatewayOpcode.PRESENCE_UPDATE,
            "d": {
                "status": status,
                "activities": activities or [],
                "afk": afk,
                "since": since if since is not None else (int(time.time() * 1000) if status == Status.IDLE else 0),
            },
        }
        await self._send(payload)

    async def set_status(self, status: str) -> None:
        await self.update_presence(status=status)

    async def set_activity(self, name: str, activity_type: int = ActivityType.PLAYING, url: Optional[str] = None, details: Optional[str] = None, state: Optional[str] = None, status: str = Status.ONLINE) -> None:
        activity: Dict[str, Any] = {"name": name, "type": activity_type}
        if url:
            activity["url"] = url
        if details:
            activity["details"] = details
        if state:
            activity["state"] = state
        await self.update_presence(status=status, activities=[activity])

    async def set_custom_status(self, text: str, emoji_name: Optional[str] = None, emoji_id: Optional[str] = None, expires_at: Optional[str] = None, status: str = Status.ONLINE) -> None:
        activity: Dict[str, Any] = {"name": "Custom Status", "type": ActivityType.CUSTOM, "state": text}
        if emoji_name or emoji_id:
            activity["emoji"] = {"name": emoji_name, "id": emoji_id}
        if expires_at:
            activity["expires_at"] = expires_at
        await self.update_presence(status=status, activities=[activity])

    async def clear_activity(self, status: str = Status.ONLINE) -> None:
        await self.update_presence(status=status, activities=[])

    async def update_voice_state(self, guild_id: str, channel_id: Optional[str] = None, self_mute: bool = False, self_deaf: bool = False, self_video: bool = False) -> None:
        payload = {
            "op": GatewayOpcode.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": self_mute,
                "self_deaf": self_deaf,
                "self_video": self_video,
            },
        }
        await self._send(payload)

    async def request_guild_members(self, guild_id: str, query: str = "", limit: int = 0, presences: bool = False, user_ids: Optional[List[str]] = None, nonce: Optional[str] = None) -> None:
        d: Dict[str, Any] = {"guild_id": guild_id, "query": query, "limit": limit, "presences": presences}
        if user_ids:
            d["user_ids"] = user_ids
        if nonce:
            d["nonce"] = nonce
        await self._send({"op": GatewayOpcode.REQUEST_GUILD_MEMBERS, "d": d})

    async def lazy_load_guild(self, guild_id: str, channels: Optional[Dict[str, Any]] = None) -> None:
        d: Dict[str, Any] = {"guild_id": guild_id}
        if channels:
            d["channels"] = channels
        await self._send({"op": GatewayOpcode.LAZY_REQUEST, "d": d})

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def close(self, code: int = GatewayCloseCode.NORMAL) -> None:
        self._connected = False
        self.auto_reconnect = False
        await self._cancel_tasks()
        if self._ws is not None:
            try:
                await self._ws.close(code)
            except Exception:
                pass
            self._ws = None
        logger.info("Gateway closed by client (code=%d, reconnects=%d, uptime=%.1fs)", code, self._reconnect_count, self.connection_uptime)

    async def _cancel_tasks(self) -> None:
        for task in (self._heartbeat_task, self._receive_task, self._event_dispatcher_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._heartbeat_task = None
        self._receive_task = None
        self._event_dispatcher_task = None

    async def __aenter__(self) -> "Gateway":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"<Gateway connected={self._connected} ready={self._ready} session={self._session_id!r} latency={self.latency * 1000:.1f}ms>"