"""
Utility functions and helpers for Dapi.

This module contains utility functions, decorators, and helper classes.
"""
import asyncio
import base64
import functools
import hashlib
import json
import logging
import random
import re
import string
import time
import urllib.parse
import warnings
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    overload,
)
from functools import wraps

from .constants import DISCORD_EPOCH


__all__ = [
    # Snowflake utilities
    'generate_snowflake',
    'parse_snowflake',
    'snowflake_to_datetime',
    'datetime_to_snowflake',

    # String utilities
    'generate_nonce',
    'generate_session_id',
    'escape_markdown',
    'unescape_markdown',
    'strip_markdown',
    'format_timestamp',
    'parse_timestamp',

    # URL utilities
    'extract_message_id',
    'extract_channel_id',
    'extract_guild_id',
    'parse_invite_url',
    'parse_emoji_url',

    # Token utilities
    'parse_token',
    'validate_token',
    'encode_token',

    # Message utilities
    'split_message',
    'mentions_all',
    'mention_user',
    'mention_channel',
    'mention_role',
    'custom_emoji',
    'timestamp_style',

    # Async utilities
    'maybe_coroutine',
    'async_contextmanager',
    'rate_limit_handler',
    'retry_handler',

    # Logging
    'setup_logging',
    'get_logger',

    # Decorators
    'deprecated',
    'experimental',

    # Other
    'calculate_permissions',
    'has_permissions',
    'format_discord_name',
]


# Setup logger
_logger = logging.getLogger('dapi')


# Snowflake utilities

def generate_snowflake(timestamp: Optional[float] = None) -> str:
    """
    Generate a Discord-style snowflake ID.

    Discord snowflakes are 64-bit integers composed of:
    - 42-bit timestamp (milliseconds since Discord epoch)
    - 5-bit worker ID
    - 5-bit process ID
    - 12-bit sequence number

    Args:
        timestamp: Unix timestamp (milliseconds). Defaults to current time.

    Returns:
        Generated snowflake ID as string.
    """
    if timestamp is None:
        timestamp = time.time() * 1000

    # Time since Discord epoch
    discord_ts = int(timestamp - DISCORD_EPOCH) << 22

    # Random worker ID (0-31)
    worker_id = random.randint(0, 31) << 17

    # Random process ID (0-31)
    process_id = random.randint(0, 31) << 12

    # Random sequence (0-4095)
    sequence = random.randint(0, 4095)

    return str(discord_ts | worker_id | process_id | sequence)


def parse_snowflake(snowflake: Union[str, int]) -> int:
    """Parse snowflake to integer."""
    return int(snowflake)


def snowflake_to_datetime(snowflake: Union[str, int]) -> datetime:
    """
    Convert snowflake to datetime.

    Args:
        snowflake: Snowflake ID.

    Returns:
        Datetime of when the snowflake was created.
    """
    sf = int(snowflake)
    timestamp = (sf >> 22) + DISCORD_EPOCH
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def datetime_to_snowflake(dt: datetime) -> str:
    """
    Convert datetime to snowflake.

    Args:
        dt: Datetime object.

    Returns:
        Snowflake ID representing the datetime.
    """
    timestamp = dt.timestamp() * 1000
    return generate_snowflake(timestamp)


# String utilities

def generate_nonce() -> str:
    """
    Generate a nonce for message sending.

    Discord requires a unique nonce for each message.

    Returns:
        Nonce string.
    """
    return str(int(time.time() * 1000))


def generate_session_id() -> str:
    """
    Generate a random session ID.

    Returns:
        Random session ID string.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(32))


def escape_markdown(text: str) -> str:
    """
    Escape Discord markdown characters.

    Args:
        text: Text to escape.

    Returns:
        Escaped text.
    """
    # Order matters - escape backslash first
    replacements = [
        ('\\', '\\\\'),
        ('*', '\\*'),
        ('_', '\\_'),
        ('~', '\\~'),
        ('`', '\\`'),
        ('|', '\\|'),
        ('>', '\\>'),
        ('#', '\\#'),
        ('+', '\\+'),
        ('-', '\\-'),
        ('=', '\\='),
        ('{', '\\{'),
        ('}', '\\}'),
        ('[', '\\]'),
        (']', '\\]'),
        ('(', '\\('),
        (')', '\\)'),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


def unescape_markdown(text: str) -> str:
    """
    Unescape Discord markdown characters.

    Args:
        text: Escaped text.

    Returns:
        Unescaped text.
    """
    patterns = [
        r'\\([*_|~`|>#={}\[\]()])',
    ]

    for pattern in patterns:
        text = re.sub(pattern, r'\1', text)

    return text


def strip_markdown(text: str) -> str:
    """Remove Discord markdown formatting."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Underline
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Strikethrough
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Code blocks
    text = re.sub(r'```(.+?)```', r'\1', text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Spoilers
    text = re.sub(r'\|\|(.+?)\|\|', r'\1', text)
    # Blockquotes
    text = re.sub(r'^>+\s?', '', text, flags=re.MULTILINE)

    return text


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime to Discord ISO format.

    Args:
        dt: Datetime object.

    Returns:
        ISO formatted string.
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """
    Parse Discord timestamp string.

    Args:
        ts: Timestamp string.

    Returns:
        Datetime object or None.
    """
    if ts is None:
        return None

    try:
        # Handle Z suffix
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


# URL utilities

def extract_message_id(url: str) -> Optional[str]:
    """
    Extract message ID from Discord URL.

    Args:
        url: Discord message URL.

    Returns:
        Message ID or None.
    """
    match = re.search(r'/channels/\d+/(\d+)/(\d+)', url)
    if match:
        return match.group(2)
    return None


def extract_channel_id(url: str) -> Optional[str]:
    """
    Extract channel ID from Discord URL.

    Args:
        url: Discord URL.

    Returns:
        Channel ID or None.
    """
    # From message URL
    match = re.search(r'/channels/\d+/(\d+)', url)
    if match:
        return match.group(1)
    # From channel URL
    match = re.search(r'/channels/(\d+)', url)
    if match:
        return match.group(1)
    return None


def extract_guild_id(url: str) -> Optional[str]:
    """
    Extract guild ID from Discord URL.

    Args:
        url: Discord URL.

    Returns:
        Guild ID or None.
    """
    match = re.search(r'/channels/(\d+)/', url)
    if match:
        return match.group(1)
    return None


def parse_invite_url(url: str) -> Optional[str]:
    """
    Extract invite code from URL.

    Args:
        url: Discord invite URL or code.

    Returns:
        Invite code or None.
    """
    # Direct code
    if re.match(r'^[a-zA-Z0-9]{2,30}$', url):
        return url

    # From URL
    match = re.search(r'(?:discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)

    return None


def parse_emoji_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse emoji from URL.

    Args:
        url: Emoji URL.

    Returns:
        Dict with emoji id, name, animated, or None.
    """
    # Custom emoji URL
    match = re.search(r'/emojis/(\d+)\.(png|gif)', url)
    if match:
        return {
            'id': match.group(1),
            'animated': match.group(2) == 'gif'
        }
    return None


# Token utilities

def parse_token(token: str) -> Dict[str, str]:
    """
    Parse Discord token into components.

    Discord tokens are base64 encoded with format:
    base64(user_id).base64(timestamp).base64(hmac)

    Args:
        token: Discord token.

    Returns:
        Dict with user_id, timestamp, hmac components.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}

        user_id = _decode_base64(parts[0])
        timestamp = _decode_base64(parts[1])
        hmac = parts[2]

        return {
            'user_id': user_id,
            'timestamp': timestamp,
            'hmac': hmac
        }
    except Exception:
        return {}


def validate_token(token: str) -> bool:
    """
    Validate Discord token format.

    Args:
        token: Token to validate.

    Returns:
        True if valid format, False otherwise.
    """
    if not token or not isinstance(token, str):
        return False

    # Token should have 3 parts
    parts = token.split('.')
    if len(parts) != 3:
        return False

    # Check base64 encoding
    try:
        for part in parts[:2]:
            _decode_base64(part)
        return True
    except Exception:
        return False


def encode_token(user_id: str, timestamp: str, hmac: str) -> str:
    """
    Encode token from components.

    Args:
        user_id: Discord user ID.
        timestamp: Timestamp string.
        hmac: HMAC string.

    Returns:
        Encoded token.
    """
    return f"{_encode_base64(user_id)}.{_encode_base64(timestamp)}.{hmac}"


def _decode_base64(data: str) -> str:
    """Decode URL-safe base64 string."""
    # Add padding if needed
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data).decode('utf-8')


def _encode_base64(data: str) -> str:
    """Encode string to URL-safe base64."""
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip('=')


# Message utilities

def split_message(
    text: str,
    max_length: int = 2000,
    split_char: str = '\n'
) -> List[str]:
    """
    Split text for Discord's message limit.

    Args:
        text: Text to split.
        max_length: Maximum message length (default 2000).
        split_char: Character to split on (default newline).

    Returns:
        List of message parts.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    for line in text.split(split_char):
        if len(current) + len(line) + 1 > max_length:
            if current:
                chunks.append(current.rstrip(split_char))
            current = line + split_char
        else:
            current += line + split_char

    if current:
        chunks.append(current.rstrip(split_char))

    return chunks


def mentions_all() -> str:
    """Return @everyone mention string."""
    return '@everyone'


def mention_user(user_id: Union[str, int], nitro: bool = False) -> str:
    """
    Create user mention.

    Args:
        user_id: User ID.
        nitro: Whether to use nickname mention (<@!id>).

    Returns:
        User mention string.
    """
    if nitro:
        return f"<@!{user_id}>"
    return f"<@{user_id}>"


def mention_channel(channel_id: Union[str, int]) -> str:
    """
    Create channel mention.

    Args:
        channel_id: Channel ID.

    Returns:
        Channel mention string.
    """
    return f"<#{channel_id}>"


def mention_role(role_id: Union[str, int]) -> str:
    """
    Create role mention.

    Args:
        role_id: Role ID.

    Returns:
        Role mention string.
    """
    return f"<@&{role_id}>"


def custom_emoji(
    emoji_id: Union[str, int],
    name: str = "",
    animated: bool = False
) -> str:
    """
    Create custom emoji string.

    Args:
        emoji_id: Emoji ID.
        name: Emoji name (optional).
        animated: Whether emoji is animated.

    Returns:
        Emoji string.
    """
    prefix = 'a' if animated else ''
    return f"<{prefix}:{name or 'emoji'}:{emoji_id}>"


def timestamp_style(
    timestamp: Union[int, float, datetime],
    style: str = 'f'
) -> str:
    """
    Create Discord timestamp.

    Styles:
        t: Short time (h:mm A)
        T: Long time (h:mm:ss A)
        d: Short date (MM/DD/YYYY)
        D: Long date (MMMM D, YYYY)
        f: Short date-time (MMMM D, YYYY h:mm A)
        F: Long date-time (dddd, MMMM D, YYYY h:mm A)
        R: Relative time (2 hours ago)

    Args:
        timestamp: Unix timestamp or datetime.
        style: Timestamp style (default 'f').

    Returns:
        Timestamp string.
    """
    if isinstance(timestamp, datetime):
        ts = int(timestamp.timestamp())
    else:
        ts = int(timestamp)

    return f"<t:{ts}:{style}>"


# Async utilities

async def maybe_coroutine(
    func: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Call function, handling if it's a coroutine.

    Args:
        func: Function to call.
        *args: Arguments.
        **kwargs: Keyword arguments.

    Returns:
        Function result.
    """
    result = func(*args, **kwargs)
    if asyncio.iscoroutine(result):
        return await result
    return result


def async_contextmanager(func: Callable) -> Callable:
    """
    Decorator to create async context manager.

    Args:
        func: Function to decorate.

    Returns:
        Async context manager.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return _AsyncContextManager(func, args, kwargs)
    return wrapper


class _AsyncContextManager:
    """Helper class for async context managers."""

    def __init__(self, func: Callable, args: tuple, kwargs: dict):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.gen = None

    async def __aenter__(self):
        self.gen = self.func(*self.args, **self.kwargs)
        return await self.gen.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.gen.__anext__()
        except StopAsyncIteration:
            pass


def rate_limit_handler(
    calls: int = 1,
    period: float = 1.0,
    key: Optional[str] = None
):
    """
    Decorator for rate limiting.

    Args:
        calls: Number of calls allowed.
        period: Time period in seconds.
        key: Rate limit key (optional).

    Returns:
        Decorator function.
    """
    _storage: Dict[str, List[float]] = {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            rate_key = key or func.__name__
            now = time.time()

            if rate_key not in _storage:
                _storage[rate_key] = []

            # Clean old calls
            _storage[rate_key] = [
                t for t in _storage[rate_key]
                if t > now - period
            ]

            # Check limit
            if len(_storage[rate_key]) >= calls:
                wait = _storage[rate_key][0] + period - now
                if wait > 0:
                    await asyncio.sleep(wait)
                _storage[rate_key] = _storage[rate_key][1:]

            _storage[rate_key].append(now)
            return await func(*args, **kwargs)

        return async_wrapper

    return decorator


def retry_handler(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry handling.

    Args:
        max_retries: Maximum retry attempts.
        delay: Initial delay between retries.
        backoff: Backoff multiplier.
        exceptions: Tuple of exceptions to catch.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return async_wrapper

    return decorator


# Logging utilities

def setup_logging(
    level: int = logging.INFO,
    format: str = None,
    file: str = None
) -> None:
    """
    Setup logging for Dapi.

    Args:
        level: Logging level.
        format: Format string.
        file: Log file path.
    """
    if format is None:
        format = '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format))

    logger = logging.getLogger('dapi')
    logger.setLevel(level)
    logger.addHandler(handler)

    if file:
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(logging.Formatter(format))
        logger.addHandler(file_handler)


def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f'dapi.{name}')
    return logging.getLogger('dapi')


# Decorators

def deprecated(message: str = None):
    """
    Mark function as deprecated.

    Args:
        message: Deprecation message.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = message or f"{func.__name__} is deprecated"
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            msg = message or f"{func.__name__} is deprecated"
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def experimental(message: str = None):
    """
    Mark function as experimental.

    Args:
        message: Experimental message.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = message or f"{func.__name__} is experimental and may change"
            warnings.warn(msg, UserWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Permission utilities

def calculate_permissions(permissions: int) -> List[str]:
    """
    Calculate permission names from permission integer.

    Args:
        permissions: Permission integer.

    Returns:
        List of permission names.
    """
    from .constants import Permissions

    result = []
    for name, value in Permissions.__dict__.items():
        if name.startswith('_'):
            continue
        if isinstance(value, int) and permissions & value:
            result.append(name)

    return result


def has_permissions(
    permissions: int,
    required: List[str]
) -> bool:
    """
    Check if permissions include required permissions.

    Args:
        permissions: Permission integer.
        required: List of required permission names.

    Returns:
        True if all permissions are present.
    """
    from .constants import Permissions

    for name in required:
        if not (permissions & getattr(Permissions, name, 0)):
            return False

    return True


# Other utilities

def format_discord_name(
    username: str,
    discriminator: Optional[str] = None
) -> str:
    """
    Format Discord username with discriminator.

    Args:
        username: Username.
        discriminator: Discriminator (optional).

    Returns:
        Formatted username string.
    """
    if discriminator and discriminator != '0':
        return f"{username}#{discriminator}"
    return username
