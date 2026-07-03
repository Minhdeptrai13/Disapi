"""
constants.py — Discord API Constants & Fingerprinting
=====================================================

All Discord API constants, enum-style classes, default headers,
Super-Properties generation, and build number fingerprinting
for realistic user client emulation.
"""

from __future__ import annotations

import base64
import json
import random
from typing import Dict, List


# ─── API Endpoints ──────────────────────────────────────────────────────────

API_VERSION: int = 10
API_BASE_URL: str = f"https://discord.com/api/v{API_VERSION}"
GATEWAY_URL: str = f"wss://gateway.discord.gg/?v={API_VERSION}&encoding=json&compress=zlib-stream"
CDN_BASE_URL: str = "https://cdn.discordapp.com"
MEDIA_PROXY_URL: str = "https://media.discordapp.net"

# Realistic build number (updated 2026)
CLIENT_BUILD_NUMBER: int = 392024
CLIENT_VERSION: str = "0.0.354"

# Discord Epoch (January 1, 2015, in ms)
DISCORD_EPOCH: int = 1_420_070_400_000

# ─── Limits ─────────────────────────────────────────────────────────────────

DEFAULT_REQUEST_TIMEOUT: float = 30.0
DEFAULT_RATE_LIMIT_RETRIES: int = 5
DEFAULT_RATE_LIMIT_DELAY: float = 0.5
DEFAULT_RATE_LIMIT_JITTER: float = 0.25

MAX_MESSAGE_LENGTH: int = 2000
MAX_EMBED_TITLE: int = 256
MAX_EMBED_DESCRIPTION: int = 4096
MAX_EMBED_FIELD_NAME: int = 256
MAX_EMBED_FIELD_VALUE: int = 1024
MAX_EMBED_FOOTER: int = 2048
MAX_EMBED_AUTHOR: int = 256
MAX_EMBEDS_PER_MESSAGE: int = 10
MAX_FIELDS_PER_EMBED: int = 25

MIN_BULK_DELETE: int = 2
MAX_BULK_DELETE: int = 100

# ─── Realistic User-Agent Pool ──────────────────────────────────────────────

# Chrome 131 / Edge 131 / Firefox 133 — realistic 2025/2026 browser versions
_CHROME_VERSIONS: List[str] = [
    "131.0.0.0", "130.0.0.0", "129.0.0.0", "128.0.6613.120",
    "127.0.6533.88", "126.0.6478.186",
]

_FIREFOX_VERSIONS: List[str] = [
    "133.0", "132.0", "131.0", "130.0",
]

USER_AGENTS: List[str] = [
    # Chrome Windows
    *(
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{v} Safari/537.36"
        for v in _CHROME_VERSIONS
    ),
    # Chrome Mac
    *(
        f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{v} Safari/537.36"
        for v in _CHROME_VERSIONS[:3]
    ),
    # Edge Windows
    *(
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{v} Safari/537.36 Edg/{v}"
        for v in _CHROME_VERSIONS[:2]
    ),
    # Firefox Windows
    *(
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{v}) "
        f"Gecko/20100101 Firefox/{v}"
        for v in _FIREFOX_VERSIONS
    ),
]

# ─── Fingerprinting ──────────────────────────────────────────────────────────

_SEC_CH_UA_MAP: Dict[str, str] = {
    "131.0.0.0": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "130.0.0.0": '"Google Chrome";v="130", "Chromium";v="130", "Not_A Brand";v="24"',
    "129.0.0.0": '"Google Chrome";v="129", "Chromium";v="129", "Not_A Brand";v="24"',
    "128.0.6613.120": '"Google Chrome";v="128", "Chromium";v="128", "Not_A Brand";v="24"',
    "127.0.6533.88": '"Google Chrome";v="127", "Chromium";v="127", "Not_A Brand";v="24"',
    "126.0.6478.186": '"Google Chrome";v="126", "Chromium";v="126", "Not_A Brand";v="24"',
}


def _pick_chrome_ua() -> tuple[str, str, str]:
    """Pick a random Chrome UA, version, and sec-ch-ua string."""
    version = random.choice(_CHROME_VERSIONS)
    ua = (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{version} Safari/537.36"
    )
    major = version.split(".")[0]
    sec_ch = _SEC_CH_UA_MAP.get(
        version,
        f'"Google Chrome";v="{major}", "Chromium";v="{major}", "Not_A Brand";v="24"',
    )
    return ua, version, sec_ch


def get_default_headers() -> Dict[str, str]:
    """Build realistic Discord HTTP request headers.

    Returns:
        Dict of HTTP headers mimicking a real Chrome browser on Discord Web.
    """
    ua, chrome_ver, sec_ch = _pick_chrome_ua()
    return {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://discord.com/channels/@me",
        "Origin": "https://discord.com",
        "Sec-Ch-Ua": sec_ch,
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": ua,
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "America/New_York",
    }


def get_super_properties(build_number: int = CLIENT_BUILD_NUMBER) -> str:
    """Generate the X-Super-Properties header value.

    Encodes browser fingerprint data as base64 JSON, exactly as the
    real Discord web client sends it.

    Args:
        build_number: Discord client build number.

    Returns:
        Base64-encoded JSON string for X-Super-Properties header.
    """
    ua, chrome_ver, _ = _pick_chrome_ua()
    major = chrome_ver.split(".")[0]

    props: Dict = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": ua,
        "browser_version": chrome_ver,
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": build_number,
        "client_event_source": None,
        "design_id": 0,
    }
    return base64.b64encode(json.dumps(props, separators=(",", ":")).encode()).decode()


def get_gateway_properties() -> Dict:
    """Get realistic client properties for Gateway IDENTIFY payload."""
    ua, chrome_ver, _ = _pick_chrome_ua()
    return {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": ua,
        "browser_version": chrome_ver,
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": CLIENT_BUILD_NUMBER,
        "client_event_source": None,
        "design_id": 0,
    }


# ─── Enum-Style Constants ────────────────────────────────────────────────────

class ActivityType:
    """Rich Presence activity type constants."""
    PLAYING: int    = 0
    STREAMING: int  = 1
    LISTENING: int  = 2
    WATCHING: int   = 3
    CUSTOM: int     = 4
    COMPETING: int  = 5


class MessageType:
    """Discord message type IDs."""
    DEFAULT: int                    = 0
    RECIPIENT_ADD: int              = 1
    RECIPIENT_REMOVE: int           = 2
    CALL: int                       = 3
    CHANNEL_NAME_CHANGE: int        = 4
    CHANNEL_ICON_CHANGE: int        = 5
    CHANNEL_PINNED_MESSAGE: int     = 6
    GUILD_MEMBER_JOIN: int          = 7
    USER_PREMIUM_GUILD_SUB: int     = 8
    USER_PREMIUM_GUILD_SUB_T1: int  = 9
    USER_PREMIUM_GUILD_SUB_T2: int  = 10
    USER_PREMIUM_GUILD_SUB_T3: int  = 11
    CHANNEL_FOLLOW_ADD: int         = 12
    GUILD_DISCOVERY_DISQUALIFIED: int = 14
    GUILD_DISCOVERY_REQUALIFIED: int  = 15
    REPLY: int                      = 19
    APPLICATION_COMMAND: int        = 20
    THREAD_STARTER_MESSAGE: int     = 21
    GUILD_INVITE_REMINDER: int      = 22
    CONTEXT_MENU_COMMAND: int       = 23
    AUTO_MODERATION_ACTION: int     = 24


class ChannelType:
    """Discord channel type IDs."""
    GUILD_TEXT: int           = 0
    DM: int                   = 1
    GUILD_VOICE: int          = 2
    GROUP_DM: int             = 3
    GUILD_CATEGORY: int       = 4
    GUILD_NEWS: int           = 5
    GUILD_NEWS_THREAD: int    = 10
    GUILD_PUBLIC_THREAD: int  = 11
    GUILD_PRIVATE_THREAD: int = 12
    GUILD_STAGE_VOICE: int    = 13
    GUILD_DIRECTORY: int      = 14
    GUILD_FORUM: int          = 15
    GUILD_MEDIA: int          = 16


class Status:
    """Online presence status strings."""
    ONLINE: str    = "online"
    IDLE: str      = "idle"
    DND: str       = "dnd"
    INVISIBLE: str = "invisible"
    OFFLINE: str   = "offline"


class PremiumType:
    """Nitro subscription tier IDs."""
    NONE: int         = 0
    NITRO_CLASSIC: int = 1
    NITRO: int        = 2
    NITRO_BASIC: int  = 3


class UserFlags:
    """Bitmask user flags."""
    DISCORD_EMPLOYEE: int             = 1 << 0
    PARTNERED_SERVER_OWNER: int       = 1 << 1
    HYPESQUAD_EVENTS: int             = 1 << 2
    BUGHUNTER_L1: int                 = 1 << 3
    HOUSE_BRAVERY: int                = 1 << 6
    HOUSE_BRILLIANCE: int             = 1 << 7
    HOUSE_BALANCE: int                = 1 << 8
    EARLY_SUPPORTER: int              = 1 << 9
    TEAM_USER: int                    = 1 << 10
    BUGHUNTER_L2: int                 = 1 << 14
    VERIFIED_BOT: int                 = 1 << 16
    EARLY_VERIFIED_BOT_DEVELOPER: int = 1 << 17
    DISCORD_CERTIFIED_MODERATOR: int  = 1 << 18
    BOT_HTTP_INTERACTIONS: int        = 1 << 19
    SPAMMER: int                      = 1 << 20
    ACTIVE_DEVELOPER: int             = 1 << 22

    @staticmethod
    def has_flag(flags: int, flag: int) -> bool:
        """Check if a flag is set."""
        return bool(flags & flag)

    @staticmethod
    def get_names(flags: int) -> List[str]:
        """Return list of set flag names."""
        mapping = {
            "DISCORD_EMPLOYEE": UserFlags.DISCORD_EMPLOYEE,
            "PARTNERED_SERVER_OWNER": UserFlags.PARTNERED_SERVER_OWNER,
            "HYPESQUAD_EVENTS": UserFlags.HYPESQUAD_EVENTS,
            "BUGHUNTER_L1": UserFlags.BUGHUNTER_L1,
            "HOUSE_BRAVERY": UserFlags.HOUSE_BRAVERY,
            "HOUSE_BRILLIANCE": UserFlags.HOUSE_BRILLIANCE,
            "HOUSE_BALANCE": UserFlags.HOUSE_BALANCE,
            "EARLY_SUPPORTER": UserFlags.EARLY_SUPPORTER,
            "TEAM_USER": UserFlags.TEAM_USER,
            "BUGHUNTER_L2": UserFlags.BUGHUNTER_L2,
            "VERIFIED_BOT": UserFlags.VERIFIED_BOT,
            "EARLY_VERIFIED_BOT_DEVELOPER": UserFlags.EARLY_VERIFIED_BOT_DEVELOPER,
            "DISCORD_CERTIFIED_MODERATOR": UserFlags.DISCORD_CERTIFIED_MODERATOR,
            "ACTIVE_DEVELOPER": UserFlags.ACTIVE_DEVELOPER,
        }
        return [name for name, val in mapping.items() if flags & val]


class Permissions:
    """Discord permission bit flags (v10)."""
    CREATE_INSTANT_INVITE: int             = 1 << 0
    KICK_MEMBERS: int                      = 1 << 1
    BAN_MEMBERS: int                       = 1 << 2
    ADMINISTRATOR: int                     = 1 << 3
    MANAGE_CHANNELS: int                   = 1 << 4
    MANAGE_GUILD: int                      = 1 << 5
    ADD_REACTIONS: int                     = 1 << 6
    VIEW_AUDIT_LOG: int                    = 1 << 7
    PRIORITY_SPEAKER: int                  = 1 << 8
    STREAM: int                            = 1 << 9
    VIEW_CHANNEL: int                      = 1 << 10
    SEND_MESSAGES: int                     = 1 << 11
    SEND_TTS_MESSAGES: int                 = 1 << 12
    MANAGE_MESSAGES: int                   = 1 << 13
    EMBED_LINKS: int                       = 1 << 14
    ATTACH_FILES: int                      = 1 << 15
    READ_MESSAGE_HISTORY: int              = 1 << 16
    MENTION_EVERYONE: int                  = 1 << 17
    USE_EXTERNAL_EMOJIS: int               = 1 << 18
    VIEW_GUILD_INSIGHTS: int               = 1 << 19
    CONNECT: int                           = 1 << 20
    SPEAK: int                             = 1 << 21
    MUTE_MEMBERS: int                      = 1 << 22
    DEAFEN_MEMBERS: int                    = 1 << 23
    MOVE_MEMBERS: int                      = 1 << 24
    USE_VAD: int                           = 1 << 25
    CHANGE_NICKNAME: int                   = 1 << 26
    MANAGE_NICKNAMES: int                  = 1 << 27
    MANAGE_ROLES: int                      = 1 << 28
    MANAGE_WEBHOOKS: int                   = 1 << 29
    MANAGE_GUILD_EXPRESSIONS: int          = 1 << 30
    USE_APPLICATION_COMMANDS: int          = 1 << 31
    REQUEST_TO_SPEAK: int                  = 1 << 32
    MANAGE_EVENTS: int                     = 1 << 33
    MANAGE_THREADS: int                    = 1 << 34
    CREATE_PUBLIC_THREADS: int             = 1 << 35
    CREATE_PRIVATE_THREADS: int            = 1 << 36
    USE_EXTERNAL_STICKERS: int             = 1 << 37
    SEND_MESSAGES_IN_THREADS: int          = 1 << 38
    USE_EMBEDDED_ACTIVITIES: int           = 1 << 39
    MODERATE_MEMBERS: int                  = 1 << 40
    VIEW_CREATOR_MONETIZATION: int         = 1 << 41
    USE_SOUNDBOARD: int                    = 1 << 42
    CREATE_GUILD_EXPRESSIONS: int          = 1 << 43
    CREATE_EVENTS: int                     = 1 << 44
    USE_EXTERNAL_SOUNDS: int               = 1 << 45
    SEND_VOICE_MESSAGES: int               = 1 << 46
    SEND_POLLS: int                        = 1 << 49

    @staticmethod
    def compute(*flags: int) -> int:
        """Compute combined permission integer."""
        result = 0
        for f in flags:
            result |= f
        return result

    @staticmethod
    def has(permissions: int, flag: int) -> bool:
        """Check if permission flag is set."""
        if permissions & Permissions.ADMINISTRATOR:
            return True
        return bool(permissions & flag)


class RelationshipType:
    """Discord relationship type IDs."""
    NONE: int              = 0
    FRIEND: int            = 1
    BLOCKED: int           = 2
    PENDING_INCOMING: int  = 3
    PENDING_OUTGOING: int  = 4
    IMPLICIT_FRIEND: int   = 5


class UserType:
    """Discord user account types."""
    NORMAL: int = 0
    BOT: int    = 1
    TEAM: int   = 2


class GatewayOpcode:
    """Gateway WebSocket opcode constants."""
    DISPATCH: int               = 0
    HEARTBEAT: int              = 1
    IDENTIFY: int               = 2
    PRESENCE_UPDATE: int        = 3
    VOICE_STATE_UPDATE: int     = 4
    RESUME: int                 = 6
    RECONNECT: int              = 7
    REQUEST_GUILD_MEMBERS: int  = 8
    INVALID_SESSION: int        = 9
    HELLO: int                  = 10
    HEARTBEAT_ACK: int          = 11
    LAZY_REQUEST: int           = 14


class GatewayCloseCode:
    """Gateway WebSocket close code constants."""
    NORMAL: int               = 1000
    GOING_AWAY: int           = 1001
    UNKNOWN_ERROR: int        = 4000
    UNKNOWN_OPCODE: int       = 4001
    DECODE_ERROR: int         = 4002
    NOT_AUTHENTICATED: int    = 4003
    AUTHENTICATION_FAILED: int = 4004
    ALREADY_AUTHENTICATED: int = 4005
    INVALID_SEQ: int          = 4007
    RATE_LIMITED: int         = 4008
    SESSION_TIMEOUT: int      = 4009
    INVALID_SHARD: int        = 4010
    SHARDING_REQUIRED: int    = 4011
    INVALID_API_VERSION: int  = 4012
    INVALID_INTENTS: int      = 4013
    DISALLOWED_INTENTS: int   = 4015

    # Close codes that should NOT trigger reconnect
    FATAL_CODES: frozenset = frozenset({
        4004,  # Authentication failed
        4010,  # Invalid shard
        4011,  # Sharding required
        4012,  # Invalid API version
        4013,  # Invalid intents
        4015,  # Disallowed intents
    })


class AuditLogEvent:
    """Discord audit log event type IDs."""
    GUILD_UPDATE: int                         = 1
    CHANNEL_CREATE: int                       = 10
    CHANNEL_UPDATE: int                       = 11
    CHANNEL_DELETE: int                       = 12
    CHANNEL_OVERWRITE_CREATE: int             = 13
    CHANNEL_OVERWRITE_UPDATE: int             = 14
    CHANNEL_OVERWRITE_DELETE: int             = 15
    MEMBER_KICK: int                          = 20
    MEMBER_PRUNE: int                         = 21
    MEMBER_BAN_ADD: int                       = 22
    MEMBER_BAN_REMOVE: int                    = 23
    MEMBER_UPDATE: int                        = 24
    MEMBER_ROLE_UPDATE: int                   = 25
    MEMBER_MOVE: int                          = 26
    MEMBER_DISCONNECT: int                    = 27
    BOT_ADD: int                              = 28
    ROLE_CREATE: int                          = 30
    ROLE_UPDATE: int                          = 31
    ROLE_DELETE: int                          = 32
    INVITE_CREATE: int                        = 40
    INVITE_UPDATE: int                        = 41
    INVITE_DELETE: int                        = 42
    WEBHOOK_CREATE: int                       = 50
    WEBHOOK_UPDATE: int                       = 51
    WEBHOOK_DELETE: int                       = 52
    EMOJI_CREATE: int                         = 60
    EMOJI_UPDATE: int                         = 61
    EMOJI_DELETE: int                         = 62
    MESSAGE_DELETE: int                       = 72
    MESSAGE_BULK_DELETE: int                  = 73
    MESSAGE_PIN: int                          = 74
    MESSAGE_UNPIN: int                        = 75
    INTEGRATION_CREATE: int                   = 80
    INTEGRATION_UPDATE: int                   = 81
    INTEGRATION_DELETE: int                   = 82
    STAGE_INSTANCE_CREATE: int                = 83
    STAGE_INSTANCE_UPDATE: int                = 84
    STAGE_INSTANCE_DELETE: int                = 85
    STICKER_CREATE: int                       = 90
    STICKER_UPDATE: int                       = 91
    STICKER_DELETE: int                       = 92
    GUILD_SCHEDULED_EVENT_CREATE: int         = 100
    GUILD_SCHEDULED_EVENT_UPDATE: int         = 101
    GUILD_SCHEDULED_EVENT_DELETE: int         = 102
    THREAD_CREATE: int                        = 110
    THREAD_UPDATE: int                        = 111
    THREAD_DELETE: int                        = 112
    APP_COMMAND_PERMISSION_UPDATE: int        = 121
    AUTO_MODERATION_RULE_CREATE: int          = 140
    AUTO_MODERATION_RULE_UPDATE: int          = 141
    AUTO_MODERATION_RULE_DELETE: int          = 142
    AUTO_MODERATION_BLOCK_MESSAGE: int        = 143
