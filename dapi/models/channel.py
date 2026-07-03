"""
models/channel.py — Discord Channel Model
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from ..utils import snowflake_to_datetime


__all__: list[str] = ["Channel", "PermissionOverwrite", "ThreadMetadata"]


@dataclass
class PermissionOverwrite:
    """A permission overwrite for a channel.

    Attributes:
        id: Snowflake ID of the role or user.
        type: 0 = role overwrite, 1 = member overwrite.
        allow: Allowed permissions bitmask as string.
        deny: Denied permissions bitmask as string.
    """

    id: str
    type: Literal[0, 1]
    allow: str = "0"
    deny: str = "0"

    @property
    def allow_int(self) -> int:
        """Allowed permissions as integer."""
        return int(self.allow)

    @property
    def deny_int(self) -> int:
        """Denied permissions as integer."""
        return int(self.deny)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PermissionOverwrite":
        return cls(
            id=d["id"],
            type=d["type"],
            allow=d.get("allow", "0"),
            deny=d.get("deny", "0"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "type": self.type, "allow": self.allow, "deny": self.deny}


@dataclass
class ThreadMetadata:
    """Metadata specific to thread channels.

    Attributes:
        archived: True if the thread is archived.
        auto_archive_duration: Minutes until auto-archive (60/1440/4320/10080).
        archive_timestamp: When archiving was last changed.
        locked: True if non-moderators cannot unarchive.
        invitable: True if non-moderators can add members (private threads).
        create_timestamp: When the thread was created (ISO8601).
    """

    archived: bool = False
    auto_archive_duration: int = 1440
    archive_timestamp: Optional[str] = None
    locked: bool = False
    invitable: bool = False
    create_timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ThreadMetadata":
        return cls(
            archived=d.get("archived", False),
            auto_archive_duration=d.get("auto_archive_duration", 1440),
            archive_timestamp=d.get("archive_timestamp"),
            locked=d.get("locked", False),
            invitable=d.get("invitable", False),
            create_timestamp=d.get("create_timestamp"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archived": self.archived,
            "auto_archive_duration": self.auto_archive_duration,
            "archive_timestamp": self.archive_timestamp,
            "locked": self.locked,
            "invitable": self.invitable,
            "create_timestamp": self.create_timestamp,
        }


@dataclass
class Channel:
    """Represents a Discord channel.

    Covers all channel types: text, voice, DM, group DM, category,
    threads, stages, and forum channels.

    Attributes:
        id: Channel snowflake ID.
        type: Channel type integer (see ``ChannelType``).
        guild_id: Guild ID (None for DMs and groups).
        name: Channel name (None for DMs).
        topic: Channel topic, or None.
        nsfw: True if the channel is marked NSFW.
        last_message_id: ID of the most recent message, or None.
        bitrate: Voice channel bitrate in bits/s.
        user_limit: Voice channel user limit (0 = unlimited).
        rate_limit_per_user: Slowmode interval in seconds.
        recipients: List of raw user dicts (DM/group only).
        icon: Group DM icon hash, or None.
        owner_id: Group DM / thread owner ID, or None.
        application_id: Application ID for bot-created groups.
        parent_id: Parent category or forum channel ID, or None.
        last_pin_timestamp: ISO8601 of last pin, or None.
        rtc_region: Voice channel RTC region, or None.
        video_quality_mode: Video quality mode integer.
        message_count: Thread message count (approximate).
        member_count: Thread member count (capped at 50).
        thread_metadata: ``ThreadMetadata`` for thread channels.
        permission_overwrites: List of ``PermissionOverwrite`` objects.
        permissions: String of computed permissions for the current user.
        position: Channel position in the sidebar.
        flags: Channel flags bitmask.
        total_message_sent: Total messages ever sent (threads).
        default_auto_archive_duration: Default auto-archive duration.
    """

    id: str
    type: int
    guild_id: Optional[str] = None
    name: Optional[str] = None
    topic: Optional[str] = None
    nsfw: bool = False
    last_message_id: Optional[str] = None
    bitrate: int = 64000
    user_limit: int = 0
    rate_limit_per_user: int = 0
    recipients: List[Dict[str, Any]] = field(default_factory=list)
    icon: Optional[str] = None
    owner_id: Optional[str] = None
    application_id: Optional[str] = None
    parent_id: Optional[str] = None
    last_pin_timestamp: Optional[str] = None
    rtc_region: Optional[str] = None
    video_quality_mode: int = 1
    message_count: Optional[int] = None
    member_count: Optional[int] = None
    thread_metadata: Optional[ThreadMetadata] = None
    permission_overwrites: List[PermissionOverwrite] = field(default_factory=list)
    permissions: Optional[str] = None
    position: int = 0
    flags: int = 0
    total_message_sent: Optional[int] = None
    default_auto_archive_duration: int = 1440

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def created_at(self) -> datetime:
        """When this channel was created."""
        return snowflake_to_datetime(self.id)

    @property
    def mention(self) -> str:
        """Channel mention string ``<#id>``."""
        return f"<#{self.id}>"

    @property
    def is_text(self) -> bool:
        """True if this is a text or news channel."""
        return self.type in (0, 5)

    @property
    def is_voice(self) -> bool:
        """True if this is a voice or stage channel."""
        return self.type in (2, 13)

    @property
    def is_dm(self) -> bool:
        """True if this is a DM or group DM."""
        return self.type in (1, 3)

    @property
    def is_thread(self) -> bool:
        """True if this is a thread."""
        return self.type in (10, 11, 12)

    @property
    def is_forum(self) -> bool:
        """True if this is a forum channel."""
        return self.type == 15

    @property
    def is_media(self) -> bool:
        """True if this is a media channel."""
        return self.type == 16

    @property
    def is_category(self) -> bool:
        """True if this is a category."""
        return self.type == 4

    @property
    def jump_url(self) -> str:
        """Discord URL to open this channel."""
        guild_part = self.guild_id or "@me"
        return f"https://discord.com/channels/{guild_part}/{self.id}"

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Channel":
        """Parse a Channel from a raw Discord API dict."""
        thread_meta = None
        if "thread_metadata" in data:
            thread_meta = ThreadMetadata.from_dict(data["thread_metadata"])

        return cls(
            id=data["id"],
            type=data.get("type", 0),
            guild_id=data.get("guild_id"),
            name=data.get("name"),
            topic=data.get("topic"),
            nsfw=data.get("nsfw", False),
            last_message_id=data.get("last_message_id"),
            bitrate=data.get("bitrate", 64000),
            user_limit=data.get("user_limit", 0),
            rate_limit_per_user=data.get("rate_limit_per_user", 0),
            recipients=data.get("recipients", []),
            icon=data.get("icon"),
            owner_id=data.get("owner_id"),
            application_id=data.get("application_id"),
            parent_id=data.get("parent_id"),
            last_pin_timestamp=data.get("last_pin_timestamp"),
            rtc_region=data.get("rtc_region"),
            video_quality_mode=data.get("video_quality_mode", 1),
            message_count=data.get("message_count"),
            member_count=data.get("member_count"),
            thread_metadata=thread_meta,
            permission_overwrites=[
                PermissionOverwrite.from_dict(o)
                for o in data.get("permission_overwrites", [])
            ],
            permissions=data.get("permissions"),
            position=data.get("position", 0),
            flags=data.get("flags", 0),
            total_message_sent=data.get("total_message_sent"),
            default_auto_archive_duration=data.get("default_auto_archive_duration", 1440),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dict."""
        d: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "guild_id": self.guild_id,
            "name": self.name,
            "topic": self.topic,
            "nsfw": self.nsfw,
            "last_message_id": self.last_message_id,
            "position": self.position,
            "flags": self.flags,
        }
        if self.permission_overwrites:
            d["permission_overwrites"] = [o.to_dict() for o in self.permission_overwrites]
        if self.thread_metadata:
            d["thread_metadata"] = self.thread_metadata.to_dict()
        return d

    def __str__(self) -> str:
        return self.name or self.id

    def __repr__(self) -> str:
        return (
            f"<Channel id={self.id!r} type={self.type} name={self.name!r} "
            f"guild_id={self.guild_id!r}>"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Channel) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# Backward compatibility alias
Overwrite = PermissionOverwrite
