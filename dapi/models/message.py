"""
models/message.py — Discord Message Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..utils import snowflake_to_datetime
from .user import User, Member
from .embed import Embed
from .channel import Channel


__all__: list[str] = [
    "Message",
    "Attachment",
    "Reaction",
    "MessageReference",
    "MessageChannel",
]


# Embed classes have been moved to models.embed


# ─── Attachment ───────────────────────────────────────────────────────────────

@dataclass
class Attachment:
    """Represents a file attachment on a message.

    Attributes:
        id: Attachment snowflake ID.
        filename: Original filename.
        description: Optional alt-text description.
        content_type: MIME type, if known.
        size: File size in bytes.
        url: CDN URL for the file.
        proxy_url: Proxied CDN URL.
        height: Image height (if image), or None.
        width: Image width (if image), or None.
        ephemeral: True if the attachment is ephemeral.
    """

    id: str
    filename: str
    size: int
    url: str
    proxy_url: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    ephemeral: bool = False

    @property
    def is_image(self) -> bool:
        """True if the attachment is an image."""
        if self.content_type:
            return self.content_type.startswith("image/")
        return self.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))

    @property
    def is_video(self) -> bool:
        """True if the attachment is a video."""
        if self.content_type:
            return self.content_type.startswith("video/")
        return self.filename.lower().endswith((".mp4", ".mov", ".webm", ".avi"))

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Attachment":
        return cls(
            id=d["id"],
            filename=d["filename"],
            size=d.get("size", 0),
            url=d.get("url", ""),
            proxy_url=d.get("proxy_url", ""),
            description=d.get("description"),
            content_type=d.get("content_type"),
            height=d.get("height"),
            width=d.get("width"),
            ephemeral=d.get("ephemeral", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "url": self.url,
            "proxy_url": self.proxy_url,
            "description": self.description,
            "content_type": self.content_type,
            "height": self.height,
            "width": self.width,
            "ephemeral": self.ephemeral,
        }

    def __repr__(self) -> str:
        return f"<Attachment id={self.id!r} filename={self.filename!r} size={self.size}>"


# ─── Reaction ─────────────────────────────────────────────────────────────────

@dataclass
class Reaction:
    """Represents a reaction on a message.

    Attributes:
        count: Number of users who reacted with this emoji.
        me: Whether the current user has reacted with this emoji.
        emoji: Dict with ``id``, ``name``, ``animated`` keys.
    """

    count: int
    me: bool
    emoji: Dict[str, Any]

    @property
    def emoji_str(self) -> str:
        """The emoji as a string suitable for the API (``name:id`` for custom, ``name`` for unicode)."""
        name = self.emoji.get("name", "")
        emoji_id = self.emoji.get("id")
        if emoji_id:
            return f"{name}:{emoji_id}"
        return name

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Reaction":
        return cls(count=d.get("count", 0), me=d.get("me", False), emoji=d.get("emoji", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"count": self.count, "me": self.me, "emoji": self.emoji}

    def __repr__(self) -> str:
        return f"<Reaction emoji={self.emoji_str!r} count={self.count} me={self.me}>"


# ─── MessageReference ─────────────────────────────────────────────────────────

@dataclass
class MessageReference:
    """A reference to another message (used for replies and crossposting).

    Attributes:
        message_id: ID of the message being referenced.
        channel_id: Channel of the referenced message.
        guild_id: Guild of the referenced message (if applicable).
        fail_if_not_exists: Raise an error if the referenced message is deleted.
    """

    message_id: Optional[str] = None
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    fail_if_not_exists: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"fail_if_not_exists": self.fail_if_not_exists}
        if self.message_id:
            d["message_id"] = self.message_id
        if self.channel_id:
            d["channel_id"] = self.channel_id
        if self.guild_id:
            d["guild_id"] = self.guild_id
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MessageReference":
        return cls(
            message_id=d.get("message_id"),
            channel_id=d.get("channel_id"),
            guild_id=d.get("guild_id"),
            fail_if_not_exists=d.get("fail_if_not_exists", False),
        )


# ─── Message ──────────────────────────────────────────────────────────────────

@dataclass
class Message:
    """Represents a Discord message.

    Attributes:
        id: Snowflake message ID.
        channel_id: Channel where the message was sent.
        guild_id: Guild ID (None for DMs).
        author: The ``User`` who sent the message.
        member: The ``Member`` object if in a guild (may be None).
        content: Text content of the message.
        timestamp: ISO8601 timestamp string.
        edited_timestamp: ISO8601 edit timestamp, or None.
        tts: True if the message uses text-to-speech.
        mention_everyone: True if ``@everyone`` or ``@here`` was mentioned.
        mention_roles: List of role IDs mentioned.
        mentions: List of ``User`` objects mentioned.
        attachments: List of ``Attachment`` objects.
        embeds: List of ``Embed`` objects.
        reactions: List of ``Reaction`` objects.
        pinned: True if the message is pinned.
        type: Message type integer (see ``MessageType``).
        message_reference: Reference to the replied-to message, or None.
        referenced_message: The actual replied-to ``Message`` object, or None.
        flags: Message flags bitmask.
        nonce: Nonce sent with the message.
        webhook_id: ID if sent by a webhook, or None.
        thread: Thread channel opened from this message, or None.
        components: List of message components.
    """

    id: str
    channel_id: str
    author: User
    content: str = ""
    guild_id: Optional[str] = None
    member: Optional[Member] = None
    timestamp: Optional[str] = None
    edited_timestamp: Optional[str] = None
    tts: bool = False
    mention_everyone: bool = False
    mention_roles: List[str] = field(default_factory=list)
    mentions: List[User] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    embeds: List[Embed] = field(default_factory=list)
    reactions: List[Reaction] = field(default_factory=list)
    pinned: bool = False
    type: int = 0
    message_reference: Optional[MessageReference] = None
    referenced_message: Optional["Message"] = None
    flags: int = 0
    nonce: Optional[Union[str, int]] = None
    webhook_id: Optional[str] = None
    thread: Optional[Dict[str, Any]] = None
    components: List[Dict[str, Any]] = field(default_factory=list)
    _client: Optional[Any] = field(default=None, repr=False)

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def created_at(self) -> datetime:
        """When this message was sent."""
        return snowflake_to_datetime(self.id)

    @property
    def jump_url(self) -> str:
        """Discord message URL for jumping to this message."""
        guild_part = self.guild_id or "@me"
        return f"https://discord.com/channels/{guild_part}/{self.channel_id}/{self.id}"

    @property
    def is_reply(self) -> bool:
        """True if this message is a reply."""
        return self.message_reference is not None

    @property
    def is_system(self) -> bool:
        """True if this is a system-generated message (join, pin, etc.)."""
        return self.type not in (0, 19, 20, 23)

    @property
    def clean_content(self) -> str:
        """Message content with mention formatting resolved to plain text."""
        content = self.content
        for user in self.mentions:
            content = content.replace(f"<@{user.id}>", f"@{user.display_name}")
            content = content.replace(f"<@!{user.id}>", f"@{user.display_name}")
        return content
    
    @property
    def channel(self) -> "MessageChannel":
        """Get the channel with send/reply methods.
        
        Returns a MessageChannel object that has send() and reply() methods.
        """
        return MessageChannel(self.channel_id, self.guild_id, self._client)
    
    async def send(self, content: Optional[str] = None, **kwargs: Any) -> "Message":
        """Send a message to this message's channel.
        
        Shortcut for message.channel.send().
        
        Args:
            content: Message content.
            **kwargs: Additional arguments (embed, tts, etc.)
            
        Returns:
            The created Message.
        """
        return await self.channel.send(content, **kwargs)
    
    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> "Message":
        """Reply to this message.
        
        Shortcut for message.channel.send() with reply_to.
        
        Args:
            content: Reply content.
            **kwargs: Additional arguments.
            
        Returns:
            The created reply Message.
        """
        return await self.channel.reply(self.id, content, **kwargs)

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Construct a Message from a raw Discord API dict."""
        author_data = data.get("author", {})
        author = User.from_dict(author_data) if author_data else User(id="0", username="Unknown")

        member: Optional[Member] = None
        member_data = data.get("member")
        if member_data and author_data:
            merged = {**member_data, "user": author_data}
            member = Member.from_dict(merged, guild_id=data.get("guild_id"))

        ref: Optional[MessageReference] = None
        ref_data = data.get("message_reference")
        if ref_data:
            ref = MessageReference.from_dict(ref_data)

        referenced_message: Optional[Message] = None
        ref_msg = data.get("referenced_message")
        if ref_msg:
            referenced_message = cls.from_dict(ref_msg)

        return cls(
            id=data["id"],
            channel_id=data["channel_id"],
            author=author,
            content=data.get("content", ""),
            guild_id=data.get("guild_id"),
            member=member,
            timestamp=data.get("timestamp"),
            edited_timestamp=data.get("edited_timestamp"),
            tts=data.get("tts", False),
            mention_everyone=data.get("mention_everyone", False),
            mention_roles=data.get("mention_roles", []),
            mentions=[User.from_dict(u) for u in data.get("mentions", [])],
            attachments=[Attachment.from_dict(a) for a in data.get("attachments", [])],
            embeds=[Embed.from_dict(e) for e in data.get("embeds", [])],
            reactions=[Reaction.from_dict(r) for r in data.get("reactions", [])],
            pinned=data.get("pinned", False),
            type=data.get("type", 0),
            message_reference=ref,
            referenced_message=referenced_message,
            flags=data.get("flags", 0),
            nonce=data.get("nonce"),
            webhook_id=data.get("webhook_id"),
            thread=data.get("thread"),
            components=data.get("components", []),
            _client=data.get("_client"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dict."""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "author": self.author.to_dict(),
            "content": self.content,
            "timestamp": self.timestamp,
            "edited_timestamp": self.edited_timestamp,
            "tts": self.tts,
            "mention_everyone": self.mention_everyone,
            "mention_roles": self.mention_roles,
            "mentions": [u.to_dict() for u in self.mentions],
            "attachments": [a.to_dict() for a in self.attachments],
            "embeds": [e.to_dict() for e in self.embeds],
            "reactions": [r.to_dict() for r in self.reactions],
            "pinned": self.pinned,
            "type": self.type,
            "flags": self.flags,
            "nonce": self.nonce,
            "webhook_id": self.webhook_id,
            "components": self.components,
        }

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id!r} channel={self.channel_id!r} "
            f"author={self.author!r} content={self.content[:50]!r}>"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Message) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ─── MessageChannel Helper ─────────────────────────────────────────────────────

class MessageChannel:
    """Helper class for message.channel.send() and message.channel.reply().
    
    This provides discord.py-like channel methods on Message objects.
    """
    
    def __init__(self, channel_id: str, guild_id: Optional[str], client: Optional[Any]):
        self.id = channel_id
        self.guild_id = guild_id
        self._client = client
    
    async def send(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        """Send a message to this channel.
        
        Args:
            content: Message content.
            **kwargs: Additional arguments (embed, tts, etc.)
            
        Returns:
            The created Message.
        """
        if self._client is None:
            raise RuntimeError("No client attached to message. Cannot send.")
        
        result = await self._client.messages.send(self.id, content=content, **kwargs)
        # Attach client to the new message
        result._client = self._client
        return result
    
    async def reply(self, message_id: str, content: Optional[str] = None, **kwargs: Any) -> Message:
        """Reply to a message in this channel.
        
        Args:
            message_id: Message ID to reply to.
            content: Reply content.
            **kwargs: Additional arguments.
            
        Returns:
            The created reply Message.
        """
        if self._client is None:
            raise RuntimeError("No client attached to message. Cannot reply.")
        
        result = await self._client.messages.reply(self.id, message_id, content=content, **kwargs)
        result._client = self._client
        return result
    
    async def get_message(self, message_id: str) -> Message:
        """Fetch a message from this channel.
        
        Args:
            message_id: Message ID to fetch.
            
        Returns:
            The Message.
        """
        if self._client is None:
            raise RuntimeError("No client attached to message. Cannot fetch.")
        
        result = await self._client.messages.get(self.id, message_id)
        result._client = self._client
        return result
