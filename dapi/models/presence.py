"""
models/presence.py — Discord Presence & Activity Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..constants import ActivityType, Status


__all__: list[str] = ["Activity", "Presence"]


@dataclass
class ActivityTimestamps:
    """Start/end timestamps for a rich presence activity."""
    start: Optional[int] = None
    end: Optional[int] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActivityTimestamps":
        return cls(start=d.get("start"), end=d.get("end"))

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.start is not None:
            d["start"] = self.start
        if self.end is not None:
            d["end"] = self.end
        return d


@dataclass
class ActivityAssets:
    """Image/text assets for rich presence."""
    large_image: Optional[str] = None
    large_text: Optional[str] = None
    small_image: Optional[str] = None
    small_text: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActivityAssets":
        return cls(
            large_image=d.get("large_image"),
            large_text=d.get("large_text"),
            small_image=d.get("small_image"),
            small_text=d.get("small_text"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "large_image": self.large_image,
            "large_text": self.large_text,
            "small_image": self.small_image,
            "small_text": self.small_text,
        }.items() if v is not None}


@dataclass
class ActivityParty:
    """Party info for rich presence (size, ID)."""
    id: Optional[str] = None
    size: Optional[List[int]] = None  # [current, max]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActivityParty":
        return cls(id=d.get("id"), size=d.get("size"))

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.id:
            d["id"] = self.id
        if self.size:
            d["size"] = self.size
        return d


@dataclass
class ActivitySecrets:
    """Rich presence secrets for join/spectate."""
    join: Optional[str] = None
    spectate: Optional[str] = None
    match: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActivitySecrets":
        return cls(join=d.get("join"), spectate=d.get("spectate"), match=d.get("match"))

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "join": self.join,
            "spectate": self.spectate,
            "match": self.match,
        }.items() if v is not None}


@dataclass
class Activity:
    """Represents a Discord rich presence activity.

    Attributes:
        name: Activity name (game name, song, etc.).
        type: ``ActivityType`` integer.
        url: Streaming URL (only valid for STREAMING type).
        created_at: Unix millisecond timestamp of when activity started.
        timestamps: Start/end time info.
        application_id: App ID for this rich presence.
        details: First detail line shown in Discord.
        state: Second detail line (also used for custom status text).
        emoji: Emoji dict for custom status (``{name, id, animated}``).
        party: Party info.
        assets: Image/text assets.
        secrets: Join/spectate secrets.
        instance: True if this is an instanced game session.
        flags: Activity flags bitmask.
        buttons: List of button dicts or labels.
    """

    name: str
    type: int = ActivityType.PLAYING
    url: Optional[str] = None
    created_at: Optional[int] = None
    timestamps: Optional[ActivityTimestamps] = None
    application_id: Optional[str] = None
    details: Optional[str] = None
    state: Optional[str] = None
    emoji: Optional[Dict[str, Any]] = None
    party: Optional[ActivityParty] = None
    assets: Optional[ActivityAssets] = None
    secrets: Optional[ActivitySecrets] = None
    instance: bool = False
    flags: int = 0
    buttons: List[Any] = field(default_factory=list)

    # ─── Factories ────────────────────────────────────────────────────────────

    @classmethod
    def playing(cls, name: str, details: Optional[str] = None, state: Optional[str] = None) -> "Activity":
        """Create a PLAYING activity.

        Args:
            name: Game / app name.
            details: Details line.
            state: State line.

        Returns:
            ``Activity`` with type PLAYING.
        """
        return cls(name=name, type=ActivityType.PLAYING, details=details, state=state)

    @classmethod
    def streaming(cls, name: str, url: str, details: Optional[str] = None) -> "Activity":
        """Create a STREAMING activity with a Twitch/YouTube URL.

        Args:
            name: Stream name.
            url: Stream URL (must be Twitch or YouTube).
            details: Details line.

        Returns:
            ``Activity`` with type STREAMING.
        """
        return cls(name=name, type=ActivityType.STREAMING, url=url, details=details)

    @classmethod
    def listening(cls, name: str, details: Optional[str] = None, state: Optional[str] = None) -> "Activity":
        """Create a LISTENING activity.

        Args:
            name: Song/podcast name.
            details: Artist or detail.
            state: Album or state.

        Returns:
            ``Activity`` with type LISTENING.
        """
        return cls(name=name, type=ActivityType.LISTENING, details=details, state=state)

    @classmethod
    def watching(cls, name: str, details: Optional[str] = None) -> "Activity":
        """Create a WATCHING activity."""
        return cls(name=name, type=ActivityType.WATCHING, details=details)

    @classmethod
    def competing(cls, name: str) -> "Activity":
        """Create a COMPETING activity."""
        return cls(name=name, type=ActivityType.COMPETING)

    @classmethod
    def custom(
        cls,
        text: str,
        emoji_name: Optional[str] = None,
        emoji_id: Optional[str] = None,
    ) -> "Activity":
        """Create a CUSTOM STATUS activity.

        Args:
            text: Status text (shown as the custom status).
            emoji_name: Unicode or custom emoji name.
            emoji_id: Custom emoji snowflake ID.

        Returns:
            ``Activity`` with type CUSTOM.
        """
        emoji: Optional[Dict[str, Any]] = None
        if emoji_name or emoji_id:
            emoji = {"name": emoji_name, "id": emoji_id}
        return cls(name="Custom Status", type=ActivityType.CUSTOM, state=text, emoji=emoji)

    # ─── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a Gateway-compatible activity dict."""
        d: Dict[str, Any] = {"name": self.name, "type": self.type}
        if self.url:
            d["url"] = self.url
        if self.details:
            d["details"] = self.details
        if self.state:
            d["state"] = self.state
        if self.emoji:
            d["emoji"] = self.emoji
        if self.timestamps:
            ts = self.timestamps.to_dict()
            if ts:
                d["timestamps"] = ts
        if self.assets:
            assets = self.assets.to_dict()
            if assets:
                d["assets"] = assets
        if self.party:
            party = self.party.to_dict()
            if party:
                d["party"] = party
        if self.secrets:
            secrets = self.secrets.to_dict()
            if secrets:
                d["secrets"] = secrets
        if self.application_id:
            d["application_id"] = self.application_id
        if self.buttons:
            d["buttons"] = self.buttons
        if self.flags:
            d["flags"] = self.flags
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Activity":
        ts = ActivityTimestamps.from_dict(d["timestamps"]) if "timestamps" in d else None
        assets = ActivityAssets.from_dict(d["assets"]) if "assets" in d else None
        party = ActivityParty.from_dict(d["party"]) if "party" in d else None
        secrets = ActivitySecrets.from_dict(d["secrets"]) if "secrets" in d else None
        return cls(
            name=d.get("name", ""),
            type=d.get("type", ActivityType.PLAYING),
            url=d.get("url"),
            created_at=d.get("created_at"),
            timestamps=ts,
            application_id=d.get("application_id"),
            details=d.get("details"),
            state=d.get("state"),
            emoji=d.get("emoji"),
            party=party,
            assets=assets,
            secrets=secrets,
            instance=d.get("instance", False),
            flags=d.get("flags", 0),
            buttons=d.get("buttons", []),
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Activity type={self.type} name={self.name!r}>"


@dataclass
class Presence:
    """Represents a user's combined presence state.

    Attributes:
        status: Online status string.
        activities: List of ``Activity`` objects.
        afk: Whether the client is AFK.
        since: Unix ms timestamp when idle began (or 0).
        client_status: Dict of per-client status strings (desktop/mobile/web).
    """

    status: str = Status.ONLINE
    activities: List[Activity] = field(default_factory=list)
    afk: bool = False
    since: int = 0
    client_status: Dict[str, str] = field(default_factory=dict)

    @property
    def custom_status(self) -> Optional[Activity]:
        """Return the first CUSTOM activity, or None."""
        for act in self.activities:
            if act.type == ActivityType.CUSTOM:
                return act
        return None

    @property
    def is_online(self) -> bool:
        """True if status is online."""
        return self.status == Status.ONLINE

    @property
    def is_idle(self) -> bool:
        """True if status is idle."""
        return self.status == Status.IDLE

    @property
    def is_dnd(self) -> bool:
        """True if status is Do Not Disturb."""
        return self.status == Status.DND

    @property
    def is_invisible(self) -> bool:
        """True if status is invisible."""
        return self.status in (Status.INVISIBLE, Status.OFFLINE)

    def to_gateway_dict(self) -> Dict[str, Any]:
        """Serialise to Gateway PRESENCE_UPDATE payload format."""
        return {
            "status": self.status,
            "activities": [a.to_dict() for a in self.activities],
            "afk": self.afk,
            "since": self.since,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Presence":
        return cls(
            status=d.get("status", Status.OFFLINE),
            activities=[Activity.from_dict(a) for a in d.get("activities", [])],
            afk=d.get("afk", False),
            since=d.get("since", 0),
            client_status=d.get("client_status", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "activities": [a.to_dict() for a in self.activities],
            "afk": self.afk,
            "since": self.since,
            "client_status": self.client_status,
        }

    def __repr__(self) -> str:
        return f"<Presence status={self.status!r} activities={len(self.activities)}>"
