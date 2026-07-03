"""
Type definitions for Dapi.

This module contains all type aliases, TypedDicts, and Protocol definitions.
"""
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    TypeVar,
    Callable,
    Awaitable,
    TypedDict,
    Literal,
    overload,
)
from datetime import datetime
from enum import IntEnum


# Type aliases
Snowflake = str
MaybeSnowflake = Optional[Snowflake]
JSONObject = Dict[str, Any]
JSONList = List[Any]
JSONType = Union[JSONObject, JSONList, str, int, float, bool, None]

# Async types
AsyncCallable = Callable[..., Awaitable[Any]]
Coro = Awaitable[Any]

# Generic types
T = TypeVar('T')
MaybeAsync = Union[T, Awaitable[T]]


class EmbedFooter(TypedDict, total=False):
    """Embed footer structure."""
    text: str
    icon_url: str
    proxy_icon_url: str


class EmbedImage(TypedDict, total=False):
    """Embed image structure."""
    url: str
    proxy_url: str
    height: int
    width: int


class EmbedThumbnail(TypedDict, total=False):
    """Embed thumbnail structure."""
    url: str
    proxy_url: str
    height: int
    width: int


class EmbedVideo(TypedDict, total=False):
    """Embed video structure."""
    url: str
    proxy_url: str
    height: int
    width: int


class EmbedProvider(TypedDict, total=False):
    """Embed provider structure."""
    name: str
    url: str


class EmbedAuthor(TypedDict, total=False):
    """Embed author structure."""
    name: str
    url: str
    icon_url: str
    proxy_icon_url: str


class EmbedField(TypedDict, total=False):
    """Embed field structure."""
    name: str
    value: str
    inline: bool


class EmbedData(TypedDict, total=False):
    """Full embed structure."""
    title: str
    type: Literal['rich', 'image', 'video', 'gifv', 'article', 'link']
    description: str
    url: str
    timestamp: str
    color: int
    footer: EmbedFooter
    image: EmbedImage
    thumbnail: EmbedThumbnail
    video: EmbedVideo
    provider: EmbedProvider
    author: EmbedAuthor
    fields: List[EmbedField]


class MessageReference(TypedDict, total=False):
    """Message reference for replies."""
    message_id: str
    channel_id: str
    guild_id: str
    fail_if_not_exists: bool


class AllowedMentions(TypedDict, total=False):
    """Allowed mentions structure."""
    parse: List[Literal['roles', 'users', 'everyone']]
    roles: List[str]
    users: List[str]
    replied_user: bool


class MessageCreateParams(TypedDict, total=False):
    """Parameters for creating a message."""
    content: str
    nonce: Union[str, int]
    tts: bool
    embeds: List[EmbedData]
    allowed_mentions: AllowedMentions
    message_reference: MessageReference
    components: List[JSONObject]
    sticker_ids: List[str]
    attachments: List[JSONObject]
    flags: int


class EditMessageParams(TypedDict, total=False):
    """Parameters for editing a message."""
    content: Optional[str]
    embeds: Optional[List[EmbedData]]
    flags: Optional[int]
    allowed_mentions: Optional[AllowedMentions]
    attachments: Optional[List[JSONObject]]


class PresenceUpdateParams(TypedDict, total=False):
    """Parameters for presence update."""
    since: int
    activities: List[JSONObject]
    status: Literal['online', 'idle', 'dnd', 'invisible']
    afk: bool


class ActivityData(TypedDict, total=False):
    """Activity structure for rich presence."""
    name: str
    type: int
    url: Optional[str]
    created_at: int
    timestamps: JSONObject
    application_id: str
    details: str
    state: str
    emoji: JSONObject
    party: JSONObject
    assets: JSONObject
    secrets: JSONObject
    instance: bool
    flags: int
    buttons: List[Union[str, JSONObject]]


class CustomStatusParams(TypedDict, total=False):
    """Custom status parameters."""
    text: str
    emoji_name: str
    emoji_id: str
    expires_at: Optional[str]


class VoiceStateParams(TypedDict, total=False):
    """Voice state update parameters."""
    guild_id: str
    channel_id: Optional[str]
    self_mute: bool
    self_deaf: bool
    self_video: bool
    request_to_speak_timestamp: str


class GuildMemberParams(TypedDict, total=False):
    """Guild member update parameters."""
    nick: Optional[str]
    roles: List[str]
    mute: bool
    deaf: bool
    communication_disabled_until: str


class CreateChannelParams(TypedDict, total=False):
    """Channel creation parameters."""
    name: str
    type: int
    topic: str
    bitrate: int
    user_limit: int
    rate_limit_per_user: int
    position: int
    permission_overwrites: List[JSONObject]
    parent_id: str
    nsfw: bool
    rtc_region: str
    video_quality_mode: int


class CreateInviteParams(TypedDict, total=False):
    """Invite creation parameters."""
    max_age: int
    max_uses: int
    temporary: bool
    unique: bool
    target_type: int
    target_user_id: str
    target_application_id: str


class CreateThreadParams(TypedDict, total=False):
    """Thread creation parameters."""
    name: str
    auto_archive_duration: Literal[60, 1440, 4320, 10080]
    type: Literal[10, 11, 12]
    invitable: bool
    rate_limit_per_user: int


class ReactionEmoji(TypedDict, total=False):
    """Reaction emoji structure."""
    id: Optional[str]
    name: str
    animated: bool


class Overwrite(TypedDict, total=False):
    """Permission overwrite structure."""
    id: str
    type: Literal[0, 1]  # 0 = role, 1 = member
    allow: str
    deny: str


class ComponentActionRow(TypedDict):
    """Action Row component."""
    type: Literal[1]
    components: List[JSONObject]


class ComponentButton(TypedDict, total=False):
    """Button component."""
    type: Literal[2]
    style: Literal[1, 2, 3, 4, 5]
    label: str
    emoji: JSONObject
    custom_id: str
    url: str
    disabled: bool


class ComponentSelectMenu(TypedDict, total=False):
    """Select menu component."""
    type: Literal[3]
    custom_id: str
    options: List[JSONObject]
    channel_types: List[int]
    placeholder: str
    min_values: int
    max_values: int
    disabled: bool


class InteractionData(TypedDict, total=False):
    """Interaction data structure."""
    id: str
    name: str
    type: int
    resolved: JSONObject
    options: List[JSONObject]
    guild_id: str
    channel_id: str
    target_id: str


class InteractionCreate(TypedDict, total=False):
    """Interaction create event structure."""
    id: str
    application_id: str
    type: int
    data: InteractionData
    token: str
    version: int
    message: JSONObject
    app_permissions: str
    locale: str
    guild_locale: str


class InteractionResponse(TypedDict, total=False):
    """Interaction response structure."""
    type: int
    data: JSONObject


class BulkDeleteParams(TypedDict):
    """Bulk delete parameters."""
    messages: List[str]


class SearchParams(TypedDict, total=False):
    """Search parameters for messages."""
    content: str
    author_id: str
    mentions: str
    has: str
    before: str
    after: str
    during: str
    channel_id: str
    sort_by: bool
    sort_order: bool
    limit: int
    offset: int


class TypingStart(TypedDict):
    """Typing start event data."""
    user_id: str
    channel_id: str
    guild_id: str
    member: JSONObject
    timestamp: int


class RelationshipAdd(TypedDict, total=False):
    """Relationship add event."""
    id: str
    nickname: str
    type: int
    user: JSONObject


class FriendSuggestion(TypedDict):
    """Friend suggestion structure."""
    user: JSONObject
    reasons: List[JSONObject]


class GatewayEvent(TypedDict, total=False):
    """Generic gateway event structure."""
    t: Optional[str]
    s: Optional[int]
    op: int
    d: JSONObject


class HeartbeatACK(TypedDict):
    """Heartbeat acknowledgment."""
    op: Literal[11]


class HelloEvent(TypedDict):
    """Hello event from gateway."""
    heartbeat_interval: int


class ReadyEvent(TypedDict, total=False):
    """Ready event data."""
    v: int
    user: JSONObject
    guilds: List[JSONObject]
    session_id: str
    resume_gateway_url: str
    shard: List[int]
    application: JSONObject
    country_code: str
    users: List[JSONObject]
    merged_members: List[List[JSONObject]]
    private_channels: List[JSONObject]
    friend_suggestion_count: int
    read_state: JSONObject
    user_guild_settings: JSONObject
    user_settings: JSONObject
    relationships: List[JSONObject]
    presences: List[JSONObject]


class ResumedEvent(TypedDict):
    """Resumed event data."""
    _trace: List[str]


class IdentifyPayload(TypedDict, total=False):
    """Gateway IDENTIFY payload."""
    token: str
    properties: JSONObject
    compress: bool
    large_threshold: int
    shard: List[int]
    presence: PresenceUpdateParams
    capabilities: int
    client_state: JSONObject


class ResumePayload(TypedDict):
    """Gateway RESUME payload."""
    token: str
    session_id: str
    seq: int


class RequestConfig(TypedDict, total=False):
    """HTTP request configuration."""
    timeout: float
    proxy: str
    headers: Dict[str, str]
    params: Dict[str, str]
    max_retries: int
    retry_delay: float


class ClientConfig(TypedDict, total=False):
    """Client configuration options."""
    proxy: str
    timeout: float
    max_retries: int
    rate_limit_retries: int
    rate_limit_delay: float
    debug: bool
    log_level: str
    suppress_warnings: bool


# Literal types for better type checking
HTTPMethod = Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
GatewayEventType = Literal[
    'READY',
    'RESUMED',
    'MESSAGE_CREATE',
    'MESSAGE_UPDATE',
    'MESSAGE_DELETE',
    'MESSAGE_DELETE_BULK',
    'MESSAGE_REACTION_ADD',
    'MESSAGE_REACTION_REMOVE',
    'MESSAGE_REACTION_REMOVE_ALL',
    'MESSAGE_REACTION_REMOVE_EMOJI',
    'CHANNEL_CREATE',
    'CHANNEL_UPDATE',
    'CHANNEL_DELETE',
    'CHANNEL_PINS_UPDATE',
    'GUILD_CREATE',
    'GUILD_UPDATE',
    'GUILD_DELETE',
    'GUILD_MEMBER_ADD',
    'GUILD_MEMBER_REMOVE',
    'GUILD_MEMBER_UPDATE',
    'GUILD_MEMBERS_CHUNK',
    'PRESENCE_UPDATE',
    'TYPING_START',
    'VOICE_STATE_UPDATE',
    'VOICE_SERVER_UPDATE',
    'RELATIONSHIP_ADD',
    'RELATIONSHIP_REMOVE',
    'INTERACTION_CREATE',
]


# Event listener type
EventListener = Callable[[JSONObject], Awaitable[None]]
SyncEventListener = Callable[[JSONObject], None]
AnyEventListener = Union[EventListener, SyncEventListener]
