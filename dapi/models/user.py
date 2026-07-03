"""
models/user.py — Discord User & Member Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..constants import PremiumType, UserFlags
from ..utils import snowflake_to_datetime


__all__: list[str] = ["User", "Member"]


@dataclass
class User:
    """Represents a Discord user account.

    Attributes:
        id: Snowflake user ID.
        username: Username (without discriminator on new accounts).
        discriminator: Legacy four-digit tag (``'0'`` for new usernames).
        global_name: New display name (may be None for legacy accounts).
        avatar: Avatar hash string, or None.
        banner: Banner hash, or None.
        accent_color: Profile accent colour integer, or None.
        bot: True if this is a bot account.
        system: True if this is a Discord system user.
        public_flags: Public user flags bitmask.
        premium_type: Nitro subscription tier.
        email: Email address (only available on ``@me`` endpoint).
        verified: Whether the email is verified.
        mfa_enabled: Whether MFA is enabled.
        locale: Account locale string.
        flags: All user flags (public + private).
    """

    id: str
    username: str
    discriminator: str = "0"
    global_name: Optional[str] = None
    avatar: Optional[str] = None
    banner: Optional[str] = None
    accent_color: Optional[int] = None
    bot: bool = False
    system: bool = False
    public_flags: int = 0
    premium_type: int = PremiumType.NONE
    email: Optional[str] = None
    verified: bool = False
    mfa_enabled: bool = False
    locale: str = "en-US"
    flags: int = 0

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def created_at(self) -> datetime:
        """When this user account was created."""
        return snowflake_to_datetime(self.id)

    @property
    def display_name(self) -> str:
        """Best available display name.

        Returns global_name (new system) if set, otherwise falls back to
        ``username#discriminator`` for legacy accounts.
        """
        if self.global_name:
            return self.global_name
        if self.discriminator and self.discriminator != "0":
            return f"{self.username}#{self.discriminator}"
        return self.username

    @property
    def mention(self) -> str:
        """Discord mention string ``<@id>``."""
        return f"<@{self.id}>"

    @property
    def avatar_url(self) -> Optional[str]:
        """CDN URL for the user's avatar, or None if no avatar."""
        if not self.avatar:
            return None
        ext = "gif" if self.avatar.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.{ext}?size=1024"

    @property
    def default_avatar_url(self) -> str:
        """Default avatar URL (shown when no avatar is set)."""
        idx = (int(self.id) >> 22) % 6
        return f"https://cdn.discordapp.com/embed/avatars/{idx}.png"

    @property
    def display_avatar_url(self) -> str:
        """Avatar URL, falling back to the default avatar."""
        return self.avatar_url or self.default_avatar_url

    @property
    def banner_url(self) -> Optional[str]:
        """CDN URL for the profile banner, or None."""
        if not self.banner:
            return None
        ext = "gif" if self.banner.startswith("a_") else "png"
        return f"https://cdn.discordapp.com/banners/{self.id}/{self.banner}.{ext}?size=1024"

    @property
    def is_nitro(self) -> bool:
        """True if the user has any Nitro subscription."""
        return self.premium_type > PremiumType.NONE

    def has_flag(self, flag: int) -> bool:
        """Check if a user-flag bit is set.

        Args:
            flag: One of the ``UserFlags.*`` constants.

        Returns:
            True if the flag is set in ``public_flags`` or ``flags``.
        """
        return bool((self.public_flags | self.flags) & flag)

    def get_flag_names(self) -> List[str]:
        """Return a list of human-readable flag names that are set."""
        return UserFlags.get_names(self.public_flags | self.flags)

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Construct a User from a Discord API response dict.

        Args:
            data: Raw API response dict.

        Returns:
            Populated ``User`` instance.
        """
        return cls(
            id=data["id"],
            username=data.get("username", ""),
            discriminator=data.get("discriminator", "0"),
            global_name=data.get("global_name"),
            avatar=data.get("avatar"),
            banner=data.get("banner"),
            accent_color=data.get("accent_color"),
            bot=data.get("bot", False),
            system=data.get("system", False),
            public_flags=data.get("public_flags", 0),
            premium_type=data.get("premium_type", PremiumType.NONE),
            email=data.get("email"),
            verified=data.get("verified", False),
            mfa_enabled=data.get("mfa_enabled", False),
            locale=data.get("locale", "en-US"),
            flags=data.get("flags", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dict suitable for JSON encoding."""
        return {
            "id": self.id,
            "username": self.username,
            "discriminator": self.discriminator,
            "global_name": self.global_name,
            "avatar": self.avatar,
            "banner": self.banner,
            "accent_color": self.accent_color,
            "bot": self.bot,
            "system": self.system,
            "public_flags": self.public_flags,
            "premium_type": self.premium_type,
            "email": self.email,
            "verified": self.verified,
            "mfa_enabled": self.mfa_enabled,
            "locale": self.locale,
            "flags": self.flags,
        }

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"<User id={self.id!r} username={self.username!r}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Member:
    """Represents a guild member (a User within a specific guild).

    Attributes:
        user: The underlying ``User`` object.
        guild_id: The guild this membership belongs to.
        nick: Guild-specific nickname, or None.
        roles: List of role IDs this member has.
        joined_at: When the member joined the guild (ISO8601 string).
        premium_since: When the member started boosting (ISO8601), or None.
        deaf: Whether the member is server-deafened.
        mute: Whether the member is server-muted.
        pending: True if the member hasn't passed screening.
        avatar: Guild-specific avatar hash, or None.
        communication_disabled_until: Timeout expiry (ISO8601), or None.
        flags: Member flag bitmask.
    """

    user: User
    guild_id: Optional[str] = None
    nick: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    joined_at: Optional[str] = None
    premium_since: Optional[str] = None
    deaf: bool = False
    mute: bool = False
    pending: bool = False
    avatar: Optional[str] = None
    communication_disabled_until: Optional[str] = None
    flags: int = 0

    # ─── Computed ────────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        """User ID (shortcut to ``user.id``)."""
        return self.user.id

    @property
    def display_name(self) -> str:
        """Guild nickname, or the user's display name."""
        return self.nick or self.user.display_name

    @property
    def mention(self) -> str:
        """Discord mention string."""
        return self.user.mention

    @property
    def is_timed_out(self) -> bool:
        """True if the member is currently timed out."""
        if not self.communication_disabled_until:
            return False
        from datetime import timezone
        try:
            from ..utils import parse_timestamp
            expiry = parse_timestamp(self.communication_disabled_until)
            if expiry:
                return expiry > datetime.now(tz=timezone.utc)
        except Exception:
            pass
        return False

    def has_role(self, role_id: str) -> bool:
        """Check if the member has a specific role.

        Args:
            role_id: Role snowflake ID.

        Returns:
            True if the role is in the member's role list.
        """
        return role_id in self.roles

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        guild_id: Optional[str] = None,
    ) -> "Member":
        """Construct a Member from a Discord API dict.

        Args:
            data: Raw member dict.
            guild_id: Guild snowflake (optional, embedded if provided).

        Returns:
            Populated ``Member`` instance.
        """
        user_data = data.get("user", {})
        user = User.from_dict(user_data) if user_data else User(id="0", username="Unknown")
        return cls(
            user=user,
            guild_id=guild_id or data.get("guild_id"),
            nick=data.get("nick"),
            roles=data.get("roles", []),
            joined_at=data.get("joined_at"),
            premium_since=data.get("premium_since"),
            deaf=data.get("deaf", False),
            mute=data.get("mute", False),
            pending=data.get("pending", False),
            avatar=data.get("avatar"),
            communication_disabled_until=data.get("communication_disabled_until"),
            flags=data.get("flags", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dict."""
        return {
            "user": self.user.to_dict(),
            "guild_id": self.guild_id,
            "nick": self.nick,
            "roles": self.roles,
            "joined_at": self.joined_at,
            "premium_since": self.premium_since,
            "deaf": self.deaf,
            "mute": self.mute,
            "pending": self.pending,
            "avatar": self.avatar,
            "communication_disabled_until": self.communication_disabled_until,
            "flags": self.flags,
        }

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return (
            f"<Member id={self.id!r} nick={self.nick!r} "
            f"guild_id={self.guild_id!r}>"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Member) and self.id == other.id and self.guild_id == other.guild_id

    def __hash__(self) -> int:
        return hash((self.id, self.guild_id))
