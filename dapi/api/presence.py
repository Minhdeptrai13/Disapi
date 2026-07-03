"""Presence API module."""
from typing import Any, Dict, List, Optional

from ..http_client import HTTPClient
from ..models.presence import Activity, Status
from ..constants import ActivityType


class PresenceAPI:
    """Presence API.

    This class provides methods for managing user presence and status.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def set_status(
        self,
        status: str = 'online',
        afk: bool = False
    ) -> None:
        """Set online status.

        Args:
            status: Status (online, idle, dnd, invisible).
            afk: Whether AFK.
        """
        payload = {
            'status': status,
            'afk': afk,
        }
        await self._http.patch('/users/@me/settings', json=payload)

    async def set_activity(
        self,
        name: str,
        activity_type: int = ActivityType.PLAYING,
        url: Optional[str] = None,
        application_id: Optional[str] = None,
        assets: Optional[Dict] = None,
        instance: bool = False,
    ) -> None:
        """Set activity/status.

        Args:
            name: Activity name.
            activity_type: Activity type (0=Playing, 1=Streaming, 2=Listening, 3=Watching).
            url: Stream URL (required for streaming type).
            application_id: Application ID.
            assets: Activity assets.
            instance: Whether this is an instance.
        """
        activity: Dict[str, Any] = {
            'name': name,
            'type': activity_type,
        }

        if activity_type == ActivityType.STREAMING and url:
            activity['url'] = url
        if application_id:
            activity['application_id'] = application_id
        if assets:
            activity['assets'] = assets
        if instance:
            activity['instance'] = True

        payload = {
            'activities': [activity],
            'status': 'online',
            'afk': False,
        }

        await self._http.patch('/users/@me/settings', json=payload)

    async def set_custom_status(
        self,
        text: Optional[str] = None,
        emoji_name: Optional[str] = None,
        emoji_id: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> None:
        """Set custom status.

        Args:
            text: Status text (max 100 chars).
            emoji_name: Emoji name.
            emoji_id: Custom emoji ID.
            expires_at: Expiry timestamp (ISO format).
        """
        custom_status: Dict[str, Any] = {}

        if text:
            custom_status['text'] = text[:100]
        if emoji_name:
            custom_status['emoji_name'] = emoji_name
        if emoji_id:
            custom_status['emoji_id'] = emoji_id
        if expires_at:
            custom_status['expires_at'] = expires_at

        payload = {
            'custom_status': custom_status if custom_status else None,
            'status': 'online',
        }

        await self._http.patch('/users/@me/settings', json=payload)

    async def clear_activity(self) -> None:
        """Clear all activities and custom status."""
        payload = {
            'activities': [],
            'custom_status': None,
            'status': 'online',
        }
        await self._http.patch('/users/@me/settings', json=payload)

    async def clear_custom_status(self) -> None:
        """Clear custom status only."""
        payload = {'custom_status': None}
        await self._http.patch('/users/@me/settings', json=payload)

    async def get_settings(self) -> Dict:
        """Get user settings.

        Returns:
            User settings.
        """
        return await self._http.get('/users/@me/settings')

    async def update_settings(self, **kwargs) -> Dict:
        """Update user settings.

        Args:
            **kwargs: Settings to update.

        Returns:
            Updated settings.
        """
        return await self._http.patch('/users/@me/settings', json=kwargs)

    # Voice state methods (requires gateway for full functionality)

    async def set_voice_state(
        self,
        guild_id: str,
        channel_id: Optional[str] = None,
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False
    ) -> None:
        """Set voice state.

        Note: This is best used with gateway connection for real-time updates.

        Args:
            guild_id: Guild ID.
            channel_id: Voice channel ID (None to disconnect).
            self_mute: Mute self.
            self_deaf: Deafen self.
            self_video: Enable video.
        """
        payload = {
            'guild_id': guild_id,
            'channel_id': channel_id,
            'self_mute': self_mute,
            'self_deaf': self_deaf,
            'self_video': self_video,
        }

        # This is typically sent through gateway, but HTTP can work
        await self._http.patch(f'/guilds/{guild_id}/members/@me', json={
            'channel_id': channel_id,
            'mute': self_mute,
            'deaf': self_deaf,
        })
