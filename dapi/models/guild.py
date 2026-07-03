"""
models/guild.py — Discord Guild, Role, Ban, and Invite Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils import snowflake_to_datetime
from .user import User


__all__: list[str] = ["Guild", "Role", "Ban", "Invite"]


@dataclass
class Role:
    """Represents a Discord guild role.

    Attributes:
        id: Role snowflake ID.
        name: Role name.
        color: Integer colour.
        hoist: Whether this role is pinned separately in the member list.
        icon: Role icon hash, or None.
        unicode_emoji: Unicode emoji for the role, or None.
        position: Position in the role hierarchy.
        permissions: Permission bitmask as a string.
        managed: True if managed by an integration.
        mentionable: True if the role can be mentioned.
        tags: Role tags dict (bot_id, integration_id, etc.).
        flags: Role flags bitmask.
    """

    id: str
    name: str
    color: int = 0
    colour: int = 0  # Alias — set same as color on init
    hoist: bool = False
    icon: Optional[str] = None
    unicode_emoji: Optional[str] = None
    position: int = 0
    permissions: str = "0"
    managed: bool = False
    mentionable: bool = False
    tags: Dict[str, Any] = field(default_factory=dict)
    flags: int = 0

    def __post_init__(self) -> None:
        if not self.colour:
            self.colour = self.color

    @property
    def mention(self) -> str:
        """Role mention string ``<@&id>``."""
        return f"<@&{self.id}>"

    @property
    def created_at(self) -> datetime:
        """When this role was created."""
        return snowflake_to_datetime(self.id)

    @property
    def permissions_int(self) -> int:
        """Permissions as an integer."""
        try:
            return int(self.permissions)
        except ValueError:
            return 0

    @property
    def is_bot_role(self) -> bool:
        """True if this role is managed by a bot integration."""
        return "bot_id" in self.tags

    @property
    def is_booster_role(self) -> bool:
        """True if this is the guild's premium subscriber (Nitro Booster) role."""
        return "premium_subscriber" in self.tags

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Role":
        color = d.get("color", 0)
        return cls(
            id=d["id"],
            name=d.get("name", ""),
            color=color,
            colour=color,
            hoist=d.get("hoist", False),
            icon=d.get("icon"),
            unicode_emoji=d.get("unicode_emoji"),
            position=d.get("position", 0),
            permissions=d.get("permissions", "0"),
            managed=d.get("managed", False),
            mentionable=d.get("mentionable", False),
            tags=d.get("tags", {}),
            flags=d.get("flags", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "hoist": self.hoist,
            "icon": self.icon,
            "unicode_emoji": self.unicode_emoji,
            "position": self.position,
            "permissions": self.permissions,
            "managed": self.managed,
            "mentionable": self.mentionable,
            "tags": self.tags,
            "flags": self.flags,
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Role id={self.id!r} name={self.name!r} position={self.position}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Role) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __lt__(self, other: "Role") -> bool:
        return self.position < other.position


@dataclass
class Ban:
    """Represents a guild ban record.

    Attributes:
        user: The banned ``User``.
        reason: Ban reason, or None.
    """

    user: User
    reason: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Ban":
        return cls(user=User.from_dict(d["user"]), reason=d.get("reason"))

    def to_dict(self) -> Dict[str, Any]:
        return {"user": self.user.to_dict(), "reason": self.reason}

    def __repr__(self) -> str:
        return f"<Ban user={self.user!r} reason={self.reason!r}>"


@dataclass
class Invite:
    """Represents a Discord invite.

    Attributes:
        code: The unique invite code.
        guild: Partial guild dict (may be None for group DM invites).
        channel: Partial channel dict.
        inviter: User who created the invite, or None.
        target_type: Invite target type integer.
        approximate_presence_count: Approximate online member count.
        approximate_member_count: Approximate total member count.
        expires_at: Expiry ISO8601 timestamp, or None.
        uses: Number of times this invite has been used.
        max_uses: Maximum uses (0 = unlimited).
        max_age: Seconds until expiry (0 = never).
        temporary: True if invite grants temporary membership.
    """

    code: str
    channel: Optional[Dict[str, Any]] = None
    guild: Optional[Dict[str, Any]] = None
    inviter: Optional[User] = None
    target_type: Optional[int] = None
    approximate_presence_count: Optional[int] = None
    approximate_member_count: Optional[int] = None
    expires_at: Optional[str] = None
    uses: int = 0
    max_uses: int = 0
    max_age: int = 0
    temporary: bool = False

    @property
    def url(self) -> str:
        """Full invite URL."""
        return f"https://discord.gg/{self.code}"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Invite":
        inviter_data = d.get("inviter")
        return cls(
            code=d["code"],
            channel=d.get("channel"),
            guild=d.get("guild"),
            inviter=User.from_dict(inviter_data) if inviter_data else None,
            target_type=d.get("target_type"),
            approximate_presence_count=d.get("approximate_presence_count"),
            approximate_member_count=d.get("approximate_member_count"),
            expires_at=d.get("expires_at"),
            uses=d.get("uses", 0),
            max_uses=d.get("max_uses", 0),
            max_age=d.get("max_age", 0),
            temporary=d.get("temporary", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "channel": self.channel,
            "guild": self.guild,
            "inviter": self.inviter.to_dict() if self.inviter else None,
            "target_type": self.target_type,
            "approximate_presence_count": self.approximate_presence_count,
            "approximate_member_count": self.approximate_member_count,
            "expires_at": self.expires_at,
            "uses": self.uses,
            "max_uses": self.max_uses,
            "max_age": self.max_age,
            "temporary": self.temporary,
        }

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f"<Invite code={self.code!r} guild={self.guild}>"


@dataclass
class Guild:
    """Represents a Discord guild (server).

    Attributes:
        id: Guild snowflake ID.
        name: Guild name.
        icon: Icon hash, or None.
        banner: Banner hash, or None.
        description: Guild description, or None.
        splash: Splash hash, or None.
        discovery_splash: Discovery splash hash, or None.
        owner_id: Snowflake ID of the guild owner.
        region: Voice region (deprecated, use channels).
        afk_channel_id: AFK voice channel ID, or None.
        afk_timeout: AFK timeout in seconds.
        verification_level: Verification level integer.
        default_message_notifications: Default notification setting integer.
        explicit_content_filter: Explicit content filter level integer.
        roles: List of ``Role`` objects.
        emojis: List of raw emoji dicts.
        stickers: List of raw sticker dicts.
        features: List of guild feature strings.
        mfa_level: MFA requirement level.
        system_channel_id: System messages channel ID, or None.
        rules_channel_id: Rules channel ID (community guilds), or None.
        max_members: Maximum members (if available).
        vanity_url_code: Vanity invite code, or None.
        premium_tier: Nitro boost level (0–3).
        premium_subscription_count: Number of Nitro boosts.
        preferred_locale: Preferred locale string.
        nsfw_level: NSFW level integer.
        approximate_member_count: Approximate member count (if requested).
        approximate_presence_count: Approximate online count (if requested).
        unavailable: True if the guild is unavailable (outage).
        large: True if the guild has many members.
    """

    id: str
    name: str
    icon: Optional[str] = None
    banner: Optional[str] = None
    description: Optional[str] = None
    splash: Optional[str] = None
    discovery_splash: Optional[str] = None
    owner_id: Optional[str] = None
    region: Optional[str] = None
    afk_channel_id: Optional[str] = None
    afk_timeout: int = 300
    verification_level: int = 0
    default_message_notifications: int = 0
    explicit_content_filter: int = 0
    roles: List[Role] = field(default_factory=list)
    emojis: List[Dict[str, Any]] = field(default_factory=list)
    stickers: List[Dict[str, Any]] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    mfa_level: int = 0
    system_channel_id: Optional[str] = None
    rules_channel_id: Optional[str] = None
    max_members: Optional[int] = None
    vanity_url_code: Optional[str] = None
    premium_tier: int = 0
    premium_subscription_count: int = 0
    preferred_locale: str = "en-US"
    nsfw_level: int = 0
    approximate_member_count: Optional[int] = None
    approximate_presence_count: Optional[int] = None
    unavailable: bool = False
    large: bool = False

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def created_at(self) -> datetime:
        """When this guild was created."""
        return snowflake_to_datetime(self.id)

    @property
    def icon_url(self) -> Optional[str]:
        """CDN URL for the guild icon."""
        if not self.icon:
            return None
        ext = "gif" if self.icon.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.{ext}?size=1024"

    @property
    def banner_url(self) -> Optional[str]:
        """CDN URL for the guild banner."""
        if not self.banner:
            return None
        return f"https://cdn.discordapp.com/banners/{self.id}/{self.banner}.png?size=1024"

    @property
    def splash_url(self) -> Optional[str]:
        """CDN URL for the guild invite splash."""
        if not self.splash:
            return None
        return f"https://cdn.discordapp.com/splashes/{self.id}/{self.splash}.png?size=1024"

    @property
    def vanity_url(self) -> Optional[str]:
        """Full vanity invite URL, or None."""
        return f"https://discord.gg/{self.vanity_url_code}" if self.vanity_url_code else None

    @property
    def is_community(self) -> bool:
        """True if the guild has the COMMUNITY feature."""
        return "COMMUNITY" in self.features

    @property
    def is_partnered(self) -> bool:
        """True if the guild is Discord-partnered."""
        return "PARTNERED" in self.features

    @property
    def is_verified(self) -> bool:
        """True if the guild is Discord-verified."""
        return "VERIFIED" in self.features

    @property
    def has_vanity_url(self) -> bool:
        """True if the guild has a vanity invite URL."""
        return "VANITY_URL" in self.features

    def get_role(self, role_id: str) -> Optional[Role]:
        """Look up a role by ID.

        Args:
            role_id: Role snowflake ID.

        Returns:
            ``Role`` if found, else None.
        """
        for role in self.roles:
            if role.id == role_id:
                return role
        return None

    def get_emoji(self, emoji_id: str) -> Optional[Dict[str, Any]]:
        """Look up an emoji by ID."""
        for emoji in self.emojis:
            if emoji.get("id") == emoji_id:
                return emoji
        return None

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Guild":
        """Construct a Guild from a raw API response dict."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            icon=data.get("icon"),
            banner=data.get("banner"),
            description=data.get("description"),
            splash=data.get("splash"),
            discovery_splash=data.get("discovery_splash"),
            owner_id=data.get("owner_id"),
            region=data.get("region"),
            afk_channel_id=data.get("afk_channel_id"),
            afk_timeout=data.get("afk_timeout", 300),
            verification_level=data.get("verification_level", 0),
            default_message_notifications=data.get("default_message_notifications", 0),
            explicit_content_filter=data.get("explicit_content_filter", 0),
            roles=[Role.from_dict(r) for r in data.get("roles", [])],
            emojis=data.get("emojis", []),
            stickers=data.get("stickers", []),
            features=data.get("features", []),
            mfa_level=data.get("mfa_level", 0),
            system_channel_id=data.get("system_channel_id"),
            rules_channel_id=data.get("rules_channel_id"),
            max_members=data.get("max_members"),
            vanity_url_code=data.get("vanity_url_code"),
            premium_tier=data.get("premium_tier", 0),
            premium_subscription_count=data.get("premium_subscription_count", 0),
            preferred_locale=data.get("preferred_locale", "en-US"),
            nsfw_level=data.get("nsfw_level", 0),
            approximate_member_count=data.get("approximate_member_count"),
            approximate_presence_count=data.get("approximate_presence_count"),
            unavailable=data.get("unavailable", False),
            large=data.get("large", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "banner": self.banner,
            "description": self.description,
            "owner_id": self.owner_id,
            "verification_level": self.verification_level,
            "roles": [r.to_dict() for r in self.roles],
            "features": self.features,
            "premium_tier": self.premium_tier,
            "premium_subscription_count": self.premium_subscription_count,
            "preferred_locale": self.preferred_locale,
            "approximate_member_count": self.approximate_member_count,
            "approximate_presence_count": self.approximate_presence_count,
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"<Guild id={self.id!r} name={self.name!r} "
            f"members={self.approximate_member_count}>"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Guild) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
