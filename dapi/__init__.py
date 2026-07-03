"""
Dapi - Professional Production-Grade Discord User API Wrapper
=============================================================

A highly modular, robust, and asynchronous Python wrapper for the Discord User API.
Built for precision tooling, advanced automation, and seamless integrations.

Features
--------
| Feature                          | Status  | Description                                      |
|----------------------------------|---------|--------------------------------------------------|
| **Advanced Fingerprinting**      | 🚀 Yes  | Bypass anti-bot detection with `x-super-properties` & JA3 spoofing |
| **Complete Gateway v10+**        | 🚀 Yes  | Zlib-stream, auto-resume, real-time presence     |
| **Modern Embeds & Stickers**     | 🚀 Yes  | Chainable Embed models, robust sticker sending   |
| **Smart Rate Limiting**          | 🚀 Yes  | Global and per-bucket intelligent sleep tracking |
| **Proxy & Networking**           | 🚀 Yes  | HTTP/SOCKS5 support out of the box               |
| **Modular Architecture**         | 🚀 Yes  | Clean, typed, and extensible codebase            |

╔═════════════════════════════════════════════════════════════════════╗
║                                                                     ║
║  ███████╗██╗   ██╗██╗██████╗ ████████╗██╗    ██╗ █████╗ ██╗██╗     ║
║  ██╔════╝██║   ██║██║██╔══██╗╚══██╔══╝██║    ██║██╔══██╗██║██║     ║
║  ███████╗██║   ██║██║██████╔╝   ██║   ██║ █╗ ██║███████║██║██║     ║
║  ╚════██║██║   ██║██║██╔══██╗   ██║   ██║███╗██║██╔══██║██║██║     ║
║  ███████║╚██████╔╝██║██║  ██║   ██║   ╚███╔███╔╝██║  ██║██║███████╗║
║  ╚══════╝ ╚═════╝ ╚═╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝║
║                                                                     ║
║                    ⚠  STRICT TOS WARNING  ⚠                         ║
║                                                                     ║
║              Developed by Minhdeptrai13                             ║
║                                                                     ║
║  Automating standard user accounts ("Selfbotting") is strictly      ║
║  prohibited by Discord's Terms of Service and Community Guidelines. ║
║  Using this library to perform actions on a normal user account     ║
║  will likely result in a permanent account suspension/termination.  ║
║                                                                     ║
║  This library is provided EXCLUSIVELY FOR EDUCATIONAL, RESEARCH,    ║
║  AND SECURITY TESTING PURPOSES. The authors assume absolutely no    ║
║  liability or responsibility for any resulting damages, account     ║
║  bans, or legal repercussions. Use at your own risk.                ║
╚═════════════════════════════════════════════════════════════════════╝

Quick Start
-----------
.. code-block:: python

    from dapi import Client, Embed

    client = Client("YOUR_DISCORD_TOKEN")

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")

    @client.event
    async def on_message(message):
        await message.channel.send("Hello from Dapi!")

    # Command Framework
    @client.command()
    async def ping(ctx):
        await ctx.reply("Pong!")

    @client.command()
    async def embedtest(ctx):
        embed = (
            Embed()
            .title("Dapi is Awesome")
            .description("Production-grade tooling.")
            .color(0x5865F2)
        )
        await ctx.send(embed=embed)

    client.run()
"""

from __future__ import annotations

import warnings as _warnings

__version__     = "3.0.0"
__author__      = "Dapi contributors"
__license__     = "MIT"
__description__ = "Production-Grade Discord User API Wrapper for Dapi"
__url__         = "https://github.com/dapi/dapi"
__python_requires__ = ">=3.11"

# ─── TOS Warning ────────────────────────────────────────────────────────────

_warnings.warn(
    "\n"
    "╔═════════════════════════════════════════════════════════════════════╗\n"
    "║                                                                     ║\n"
    "║  ____  _    _    Developed by Minhdeptrai13                       ║\n"
    "║ |  _ \\| |  (_)   ██████╗  █████╗ ██████╗ ██╗                     ║\n"
    "║ | | | | |  | |   ██╔══██╗██╔══██╗██╔══██╗██║                     ║\n"
    "║ | |_| | |__| |   ██║  ██║███████║██████╔╝██║                     ║\n"
    "║ |____/|_____|   ██║  ██║██╔══██║██╔══    ██║                     ║\n"
    "║                 ██████╔╝██║  ██║██║      ██                ║\n"
    "║                 ╚═════╝ ╚═╝  ╚═╝╚═╝                     ║\n"
    "║                                                                     ║\n"
    "║                    ⚠  STRICT TOS WARNING  ⚠                         ║\n"
    "║                                                                     ║\n"
    "║              Developed by Minhdeptrai13                             ║\n"
    "║                                                                     ║\n"
    "║  Selfbotting violates Discord's Terms of Service.                   ║\n"
    "║  Your account may be permanently terminated without notice.         ║\n"
    "║  This library is for EDUCATIONAL PURPOSES ONLY.                     ║\n"
    "║  Use entirely at your own risk. Authors take no liability.          ║\n"
    "╚═════════════════════════════════════════════════════════════════════╝",
    UserWarning,
    stacklevel=2,
)

# ─── Core Client ────────────────────────────────────────────────────────────

from .client import Client, SyncClient, ClientOptions

# ─── Commands Extension ───────────────────────────────────────────────────────

try:
    from .ext.commands import Context, Command, Bot
except ImportError:
    Context = None  # type: ignore[assignment, misc]
    Command = None  # type: ignore[assignment, misc]
    Bot = None  # type: ignore[assignment, misc]

# ─── HTTP + Gateway ─────────────────────────────────────────────────────────

from .http_client import HTTPClient, Route
from .rate_limiter import RateLimiter, RateLimitInfo

# ─── Constants ──────────────────────────────────────────────────────────────

from .constants import (
    API_VERSION,
    API_BASE_URL,
    GATEWAY_URL,
    ActivityType,
    ChannelType,
    Status,
    UserType,
    PremiumType,
    UserFlags,
    Permissions,
    RelationshipType,
    MessageType,
    GatewayOpcode,
    GatewayCloseCode,
    AuditLogEvent,
)

# ─── Exceptions ─────────────────────────────────────────────────────────────

from .exceptions import (
    DapiException,
    DiscordException,
    HTTPException,
    RateLimited,
    Unauthorized,
    Forbidden,
    NotFound,
    BadRequest,
    Conflict,
    MethodNotAllowed,
    ServerError,
    GatewayException,
    ConnectionClosed,
    InvalidArgument,
    InvalidToken,
    MaxConcurrencyReached,
    ResponseCorrupt,
    ConfigurationError,
    LoginFailure,
)

# ─── Models ─────────────────────────────────────────────────────────────────

from .models import (
    User,
    Member,
    Message,
    Attachment,
    Reaction,
    MessageReference,
    Channel,
    Guild,
    Role,
    Activity,
    Presence,
)
from .models.channel import PermissionOverwrite
from .models.guild import Ban, Invite
from .models.embed import Embed

# ─── Utils ──────────────────────────────────────────────────────────────────

from .utils import (
    generate_snowflake,
    parse_snowflake,
    snowflake_to_datetime,
    generate_nonce,
    escape_markdown,
    strip_markdown,
    mention_user,
    mention_channel,
    mention_role,
    custom_emoji,
    timestamp_style,
    split_message,
    validate_token,
    setup_logging,
)

# ─── Gateway (optional dep) ─────────────────────────────────────────────────

try:
    from .gateway import Gateway, GatewayConfig, EventType
except ImportError:
    Gateway = None      # type: ignore[assignment, misc]
    GatewayConfig = None  # type: ignore[assignment, misc]
    EventType = None    # type: ignore[assignment, misc]

# ─── Public API ─────────────────────────────────────────────────────────────

__all__: list[str] = [
    # Meta
    "__version__",
    "__author__",
    "__license__",
    "__description__",

    # Client
    "Client",
    "SyncClient",
    "ClientOptions",
    
    # Commands
    "Context",
    "Command",
    "Bot",

    # HTTP
    "HTTPClient",
    "Route",
    "RateLimiter",
    "RateLimitInfo",

    # Constants
    "API_VERSION",
    "API_BASE_URL",
    "GATEWAY_URL",
    "ActivityType",
    "ChannelType",
    "Status",
    "UserType",
    "PremiumType",
    "UserFlags",
    "Permissions",
    "RelationshipType",
    "MessageType",
    "GatewayOpcode",
    "GatewayCloseCode",
    "AuditLogEvent",

    # Exceptions
    "DapiException",
    "DiscordException",
    "HTTPException",
    "RateLimited",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "BadRequest",
    "Conflict",
    "MethodNotAllowed",
    "ServerError",
    "GatewayException",
    "ConnectionClosed",
    "InvalidArgument",
    "InvalidToken",
    "MaxConcurrencyReached",
    "ResponseCorrupt",
    "ConfigurationError",
    "LoginFailure",

    # Models
    "User",
    "Member",
    "Message",
    "Embed",
    "Attachment",
    "Reaction",
    "MessageReference",
    "Channel",
    "Guild",
    "Role",
    "Activity",
    "Presence",
    "PermissionOverwrite",
    "Ban",
    "Invite",

    # Utils
    "generate_snowflake",
    "parse_snowflake",
    "snowflake_to_datetime",
    "generate_nonce",
    "escape_markdown",
    "strip_markdown",
    "mention_user",
    "mention_channel",
    "mention_role",
    "custom_emoji",
    "timestamp_style",
    "split_message",
    "validate_token",
    "setup_logging",

    # Gateway
    "Gateway",
    "GatewayConfig",
    "EventType",
]
