"""
models/__init__.py — Public Models Package
"""

from .user import User, Member
from .message import (
    Message,
    Attachment,
    Reaction,
    MessageReference,
)
from .embed import (
    Embed,
    EmbedField,
    EmbedAuthor,
    EmbedFooter,
    EmbedImage,
)
from .guild import Guild, Role, Ban, Invite
from .channel import Channel, PermissionOverwrite, ThreadMetadata
from .presence import Activity, Presence

__all__: list[str] = [
    "User",
    "Member",
    "Message",
    "Embed",
    "EmbedField",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedImage",
    "Attachment",
    "Reaction",
    "MessageReference",
    "Guild",
    "Role",
    "Ban",
    "Invite",
    "Channel",
    "PermissionOverwrite",
    "ThreadMetadata",
    "Activity",
    "Presence",
]
