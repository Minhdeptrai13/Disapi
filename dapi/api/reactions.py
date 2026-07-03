"""Reactions API module."""
import urllib.parse
from typing import List

from ..http_client import HTTPClient
from ..models.user import User


class ReactionsAPI:
    """Reactions API.

    This class provides methods for interacting with Discord's reaction endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def add(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> None:
        """Add a reaction to a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji string or unicode emoji.

        Example:
            # Unicode emoji
            await client.reactions.add('123', '456', '👍')

            # Custom emoji
            await client.reactions.add('123', '456', 'custom:123456789')
        """
        encoded = urllib.parse.quote(emoji)
        await self._http.put(
            f'/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/@me'
        )

    async def remove(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        user_id: str = '@me'
    ) -> None:
        """Remove a reaction from a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji string.
            user_id: User ID to remove reaction from ('@me' for self).
        """
        encoded = urllib.parse.quote(emoji)
        await self._http.delete(
            f'/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/{user_id}'
        )

    async def remove_all(
        self,
        channel_id: str,
        message_id: str
    ) -> None:
        """Remove all reactions from a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
        """
        await self._http.delete(
            f'/channels/{channel_id}/messages/{message_id}/reactions'
        )

    async def remove_all_emoji(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> None:
        """Remove all reactions of a specific emoji.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji to remove.
        """
        encoded = urllib.parse.quote(emoji)
        await self._http.delete(
            f'/channels/{channel_id}/messages/{message_id}/reactions/{encoded}'
        )

    async def get(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        limit: int = 100,
        after: str = None
    ) -> List[User]:
        """Get users who reacted with an emoji.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji to check.
            limit: Max users to return.
            after: Get users after this ID.

        Returns:
            List of Users who reacted.
        """
        params = {'limit': limit}
        if after:
            params['after'] = after

        encoded = urllib.parse.quote(emoji)
        data = await self._http.get(
            f'/channels/{channel_id}/messages/{message_id}/reactions/{encoded}',
            params=params
        )
        return [User.from_dict(u) for u in data]
