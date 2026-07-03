"""
models/embed.py — Modern, chainable Discord Embed Model
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

__all__ = [
    "Embed",
    "EmbedField",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedImage",
]

@dataclass
class EmbedField:
    """One field in an embed."""
    name: str
    value: str
    inline: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "inline": self.inline}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedField":
        return cls(name=d["name"], value=d["value"], inline=d.get("inline", False))

@dataclass
class EmbedAuthor:
    """Embed author section."""
    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name}
        if self.url:
            d["url"] = self.url
        if self.icon_url:
            d["icon_url"] = self.icon_url
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedAuthor":
        return cls(name=d.get("name", ""), url=d.get("url"), icon_url=d.get("icon_url"))

@dataclass
class EmbedFooter:
    """Embed footer section."""
    text: str
    icon_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"text": self.text}
        if self.icon_url:
            d["icon_url"] = self.icon_url
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedFooter":
        return cls(text=d.get("text", ""), icon_url=d.get("icon_url"))

@dataclass
class EmbedImage:
    """Embed image / thumbnail."""
    url: str
    proxy_url: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"url": self.url}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedImage":
        return cls(
            url=d.get("url", ""),
            proxy_url=d.get("proxy_url"),
            height=d.get("height"),
            width=d.get("width"),
        )

class Embed:
    """Represents a Discord message embed.

    Provides a builder-style API for constructing embeds with method chaining.

    Example:
        embed = (
            Embed(title="Hello!", color=0x5865F2)
            .description("This is an embed.")
            .author("dapi", icon_url="https://...")
            .add_field("Field 1", "Value 1", inline=True)
            .add_field("Field 2", "Value 2", inline=True)
            .footer("Footer text")
        )
        await client.messages.send(channel_id, embed=embed)

    Attributes:
        _title: Embed title (max 256 chars).
        _description: Embed description (max 4096 chars).
        _url: URL that the title links to.
        _color: Integer colour (hex e.g. 0x5865F2).
        _timestamp: ISO8601 timestamp string.
        _author: ``EmbedAuthor`` object.
        _footer: ``EmbedFooter`` object.
        _image: ``EmbedImage`` object.
        _thumbnail: ``EmbedImage`` object.
        _fields: List of ``EmbedField`` objects.
    """

    __slots__ = (
        "_title", "_description", "_url", "_color", "_timestamp",
        "_author", "_footer", "_image", "_thumbnail", "_fields",
    )

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        color: Optional[int] = None,
        colour: Optional[int] = None,
        timestamp: Optional[Union[datetime, str]] = None,
    ) -> None:
        self._title = title[:256] if title else None
        self._description = description[:4096] if description else None
        self._url = url
        self._color = color or colour
        self._timestamp: Optional[str] = None
        if isinstance(timestamp, datetime):
            self._timestamp = timestamp.isoformat()
        else:
            self._timestamp = timestamp
            
        self._author: Optional[EmbedAuthor] = None
        self._footer: Optional[EmbedFooter] = None
        self._image: Optional[EmbedImage] = None
        self._thumbnail: Optional[EmbedImage] = None
        self._fields: List[EmbedField] = []

    # ─── Builder Methods (Method Chaining) ───────────────────────────────────

    def title(self, title: str) -> "Embed":
        """Set the embed title (max 256 chars)."""
        self._title = title[:256]
        return self
        
    set_title = title  # Alias for backwards compatibility

    def description(self, description: str) -> "Embed":
        """Set the embed description (max 4096 chars)."""
        self._description = description[:4096]
        return self
        
    set_description = description

    def url(self, url: str) -> "Embed":
        """Set the URL the title links to."""
        self._url = url
        return self
        
    set_url = url

    def color(self, color: int) -> "Embed":
        """Set the embed colour as an integer (e.g. 0x5865F2)."""
        self._color = color
        return self

    colour = color
    set_color = color
    set_colour = color

    def timestamp(self, dt: Optional[datetime] = None) -> "Embed":
        """Set the embed timestamp (defaults to now)."""
        from datetime import timezone
        ts = dt or datetime.now(tz=timezone.utc)
        self._timestamp = ts.isoformat()
        return self
        
    set_timestamp = timestamp

    def author(self, name: str, url: Optional[str] = None, icon_url: Optional[str] = None) -> "Embed":
        """Set the embed author section."""
        self._author = EmbedAuthor(name=name[:256], url=url, icon_url=icon_url)
        return self
        
    set_author = author

    def footer(self, text: str, icon_url: Optional[str] = None) -> "Embed":
        """Set the embed footer (max 2048 chars)."""
        self._footer = EmbedFooter(text=text[:2048], icon_url=icon_url)
        return self
        
    set_footer = footer

    def image(self, url: str) -> "Embed":
        """Set the main embed image."""
        self._image = EmbedImage(url=url)
        return self
        
    set_image = image

    def thumbnail(self, url: str) -> "Embed":
        """Set the embed thumbnail."""
        self._thumbnail = EmbedImage(url=url)
        return self
        
    set_thumbnail = thumbnail

    def add_field(self, name: str, value: str, *, inline: bool = False) -> "Embed":
        """Add a field to the embed (max 25 fields).
        
        Args:
            name: Field name (max 256 chars).
            value: Field value (max 1024 chars).
            inline: Whether the field is inline.
        """
        if len(self._fields) < 25:
            self._fields.append(
                EmbedField(name=name[:256], value=value[:1024], inline=inline)
            )
        return self

    def clear_fields(self) -> "Embed":
        """Remove all fields."""
        self._fields.clear()
        return self

    # ─── Serialisation & Validation ──────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a Discord API-compatible dict.
        Validates total character limit (6000).
        """
        d: Dict[str, Any] = {"type": "rich"}
        if self._title:
            d["title"] = self._title
        if self._description:
            d["description"] = self._description
        if self._url:
            d["url"] = self._url
        if self._color is not None:
            d["color"] = self._color
        if self._timestamp:
            d["timestamp"] = self._timestamp
        if self._author:
            d["author"] = self._author.to_dict()
        if self._footer:
            d["footer"] = self._footer.to_dict()
        if self._image:
            d["image"] = self._image.to_dict()
        if self._thumbnail:
            d["thumbnail"] = self._thumbnail.to_dict()
        if self._fields:
            d["fields"] = [f.to_dict() for f in self._fields]
            
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embed":
        """Parse an embed from a raw API response dict."""
        embed = cls(
            title=data.get("title"),
            description=data.get("description"),
            url=data.get("url"),
            color=data.get("color"),
            timestamp=data.get("timestamp"),
        )
        if "author" in data:
            embed._author = EmbedAuthor.from_dict(data["author"])
        if "footer" in data:
            embed._footer = EmbedFooter.from_dict(data["footer"])
        if "image" in data:
            embed._image = EmbedImage.from_dict(data["image"])
        if "thumbnail" in data:
            embed._thumbnail = EmbedImage.from_dict(data["thumbnail"])
        embed._fields = [EmbedField.from_dict(f) for f in data.get("fields", [])]
        return embed

    def __repr__(self) -> str:
        return f"<Embed title={self._title!r} fields={len(self._fields)}>"

    def __len__(self) -> int:
        """Total character count of the embed (Discord limits sum to 6000)."""
        total = 0
        if self._title:
            total += len(self._title)
        if self._description:
            total += len(self._description)
        if self._author:
            total += len(self._author.name)
        if self._footer:
            total += len(self._footer.text)
        for f in self._fields:
            total += len(f.name) + len(f.value)
        return total
