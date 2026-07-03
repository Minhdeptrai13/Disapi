"""Channels API module."""
from typing import Any, Dict, List, Optional

from ..http_client import HTTPClient
from ..models.channel import Channel
from ..constants import ChannelType


class ChannelsAPI:
    """Channels API.

    This class provides methods for interacting with Discord's channel endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def get(self, channel_id: str) -> Channel:
        """Get channel by ID.

        Args:
            channel_id: Channel ID.

        Returns:
            Channel object.
        """
        data = await self._http.get(f'/channels/{channel_id}')
        return Channel.from_dict(data)

    async def modify(
        self,
        channel_id: str,
        name: Optional[str] = None,
        type: Optional[int] = None,
        position: Optional[int] = None,
        topic: Optional[str] = None,
        nsfw: Optional[bool] = None,
        rate_limit_per_user: Optional[int] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
        parent_id: Optional[str] = None,
        rtc_region: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Channel:
        """Modify channel.

        Args:
            channel_id: Channel ID.
            name: New name.
            type: Channel type (convert between text/news).
            position: New position.
            topic: New topic.
            nsfw: NSFW flag.
            rate_limit_per_user: Slowmode seconds.
            bitrate: Voice bitrate.
            user_limit: Voice user limit.
            parent_id: Category ID.
            rtc_region: Voice region.
            reason: Audit log reason.

        Returns:
            Modified Channel.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload['name'] = name
        if type is not None:
            payload['type'] = type
        if position is not None:
            payload['position'] = position
        if topic is not None:
            payload['topic'] = topic
        if nsfw is not None:
            payload['nsfw'] = nsfw
        if rate_limit_per_user is not None:
            payload['rate_limit_per_user'] = rate_limit_per_user
        if bitrate is not None:
            payload['bitrate'] = bitrate
        if user_limit is not None:
            payload['user_limit'] = user_limit
        if parent_id is not None:
            payload['parent_id'] = parent_id
        if rtc_region is not None:
            payload['rtc_region'] = rtc_region

        data = await self._http.patch(
            f'/channels/{channel_id}',
            json=payload,
            reason=reason
        )
        return Channel.from_dict(data)

    async def delete(
        self,
        channel_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Delete channel (or leave DM).

        Args:
            channel_id: Channel ID.
            reason: Audit log reason.
        """
        await self._http.delete(f'/channels/{channel_id}', reason=reason)

    async def create_invite(
        self,
        channel_id: str,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: Optional[int] = None,
        target_user_id: Optional[str] = None,
        target_application_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """Create channel invite.

        Args:
            channel_id: Channel ID.
            max_age: Seconds until expiry (0 = never).
            max_uses: Max uses (0 = unlimited).
            temporary: Grant temporary membership.
            unique: Create unique invite.
            target_type: Target type for embedded applications.
            target_user_id: Target user ID.
            target_application_id: Target application ID.
            reason: Audit log reason.

        Returns:
            Invite object.
        """
        payload: Dict[str, Any] = {
            'max_age': max_age,
            'max_uses': max_uses,
            'temporary': temporary,
            'unique': unique,
        }
        if target_type is not None:
            payload['target_type'] = target_type
        if target_user_id:
            payload['target_user_id'] = target_user_id
        if target_application_id:
            payload['target_application_id'] = target_application_id

        return await self._http.post(
            f'/channels/{channel_id}/invites',
            json=payload,
            reason=reason
        )

    async def get_invites(self, channel_id: str) -> List[Dict]:
        """Get channel invites.

        Args:
            channel_id: Channel ID.

        Returns:
            List of invites.
        """
        return await self._http.get(f'/channels/{channel_id}/invites')

    # Thread methods

    async def start_thread(
        self,
        channel_id: str,
        name: str,
        auto_archive_duration: int = 1440,
        type: Optional[int] = None,
        invitable: Optional[bool] = None,
        rate_limit_per_user: Optional[int] = None,
        message_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Channel:
        """Start a thread.

        Args:
            channel_id: Channel ID.
            name: Thread name.
            auto_archive_duration: Auto archive duration (60, 1440, 4320, 10080).
            type: Thread type (public=11, private=12, auto from channel).
            invitable: Whether non-mods can invite.
            rate_limit_per_user: Slowmode.
            message_id: Message ID to convert to thread.
            reason: Audit log reason.

        Returns:
            Created Thread.
        """
        payload: Dict[str, Any] = {
            'name': name,
            'auto_archive_duration': auto_archive_duration,
        }
        if type is not None:
            payload['type'] = type
        if invitable is not None:
            payload['invitable'] = invitable
        if rate_limit_per_user is not None:
            payload['rate_limit_per_user'] = rate_limit_per_user

        if message_id:
            data = await self._http.post(
                f'/channels/{channel_id}/messages/{message_id}/threads',
                json=payload,
                reason=reason
            )
        else:
            data = await self._http.post(
                f'/channels/{channel_id}/threads',
                json=payload,
                reason=reason
            )

        return Channel.from_dict(data)

    async def join_thread(self, channel_id: str) -> None:
        """Join a thread.

        Args:
            channel_id: Thread ID.
        """
        await self._http.put(f'/channels/{channel_id}/thread-members/@me')

    async def leave_thread(self, channel_id: str) -> None:
        """Leave a thread.

        Args:
            channel_id: Thread ID.
        """
        await self._http.delete(f'/channels/{channel_id}/thread-members/@me')

    async def add_thread_member(
        self,
        channel_id: str,
        user_id: str
    ) -> None:
        """Add a member to a thread.

        Args:
            channel_id: Thread ID.
            user_id: User ID.
        """
        await self._http.put(f'/channels/{channel_id}/thread-members/{user_id}')

    async def remove_thread_member(
        self,
        channel_id: str,
        user_id: str
    ) -> None:
        """Remove a member from a thread.

        Args:
            channel_id: Thread ID.
            user_id: User ID.
        """
        await self._http.delete(f'/channels/{channel_id}/thread-members/{user_id}')

    async def get_thread_member(
        self,
        channel_id: str,
        user_id: str
    ) -> Dict:
        """Get a thread member.

        Args:
            channel_id: Thread ID.
            user_id: User ID.

        Returns:
            Thread member.
        """
        return await self._http.get(f'/channels/{channel_id}/thread-members/{user_id}')

    async def get_thread_members(self, channel_id: str) -> List[Dict]:
        """Get thread members.

        Args:
            channel_id: Thread ID.

        Returns:
            List of thread members.
        """
        return await self._http.get(f'/channels/{channel_id}/thread-members')

    async def get_public_archived_threads(
        self,
        channel_id: str,
        limit: int = 100,
        before: Optional[str] = None
    ) -> Dict:
        """Get public archived threads.

        Args:
            channel_id: Channel ID.
            limit: Max results.
            before: Timestamp to get threads before.

        Returns:
            Archived threads data.
        """
        params = {'limit': limit}
        if before:
            params['before'] = before
        return await self._http.get(
            f'/channels/{channel_id}/threads/archived/public',
            params=params
        )

    async def get_private_archived_threads(
        self,
        channel_id: str,
        limit: int = 100,
        before: Optional[str] = None
    ) -> Dict:
        """Get private archived threads.

        Args:
            channel_id: Channel ID.
            limit: Max results.
            before: Timestamp.

        Returns:
            Archived threads data.
        """
        params = {'limit': limit}
        if before:
            params['before'] = before
        return await self._http.get(
            f'/channels/{channel_id}/threads/archived/private',
            params=params
        )

    # Webhook methods

    async def create_webhook(
        self,
        channel_id: str,
        name: str,
        avatar: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """Create a webhook.

        Args:
            channel_id: Channel ID.
            name: Webhook name.
            avatar: Avatar data URI.
            reason: Audit log reason.

        Returns:
            Webhook object.
        """
        payload: Dict[str, Any] = {'name': name}
        if avatar:
            payload['avatar'] = avatar

        return await self._http.post(
            f'/channels/{channel_id}/webhooks',
            json=payload,
            reason=reason
        )

    async def get_webhooks(self, channel_id: str) -> List[Dict]:
        """Get channel webhooks.

        Args:
            channel_id: Channel ID.

        Returns:
            List of webhooks.
        """
        return await self._http.get(f'/channels/{channel_id}/webhooks')
