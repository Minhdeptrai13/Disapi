"""Relationships API module."""
from typing import Dict, List, Optional

from ..http_client import HTTPClient
from ..constants import RelationshipType


class RelationshipsAPI:
    """Relationships API.

    This class provides methods for interacting with Discord's relationship endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def get_relationships(self) -> List[Dict]:
        """Get all relationships.

        Returns:
            List of relationship objects.
        """
        return await self._http.get('/users/@me/relationships')

    async def send_friend_request(
        self,
        username: str,
        discriminator: Optional[str] = None
    ) -> Dict:
        """Send a friend request.

        Args:
            username: Username (with or without discriminator).
            discriminator: Discriminator (optional if included in username).

        Returns:
            Relationship object.
        """
        # Parse username
        if '#' in username and not discriminator:
            username, discriminator = username.rsplit('#', 1)

        payload = {'username': username}
        if discriminator:
            payload['discriminator'] = discriminator

        return await self._http.post(
            '/users/@me/relationships',
            json=payload
        )

    async def accept_friend_request(self, user_id: str) -> Dict:
        """Accept a friend request.

        Args:
            user_id: User ID.

        Returns:
            Relationship object.
        """
        return await self._http.put(f'/users/@me/relationships/{user_id}')

    async def remove_relationship(self, user_id: str) -> None:
        """Remove a relationship (unfriend, decline request).

        Args:
            user_id: User ID.
        """
        await self._http.delete(f'/users/@me/relationships/{user_id}')

    async def block_user(self, user_id: str) -> None:
        """Block a user.

        Args:
            user_id: User ID.
        """
        await self._http.put(
            f'/users/@me/relationships/{user_id}',
            json={'type': RelationshipType.BLOCKED}
        )

    async def unblock_user(self, user_id: str) -> None:
        """Unblock a user.

        Args:
            user_id: User ID.
        """
        await self._http.delete(f'/users/@me/relationships/{user_id}')

    async def get_friend_suggestions(self) -> List[Dict]:
        """Get friend suggestions.

        Returns:
            List of friend suggestions.
        """
        # This is from gateway data usually, but there may be an endpoint
        # Return empty for now if not available
        try:
            return await self._http.get('/users/@me/relationships/suggestions')
        except Exception:
            return []

    async def get_mutual_friends(self, user_id: str) -> List[Dict]:
        """Get mutual friends with a user.

        Args:
            user_id: User ID.

        Returns:
            List of mutual friends.
        """
        return await self._http.get(f'/users/{user_id}/relationships')

    async def get_mutual_guilds(self, user_id: str) -> List[Dict]:
        """Get mutual guilds with a user.

        Args:
            user_id: User ID.

        Returns:
            List of mutual guilds.
        """
        return await self._http.get(f'/users/{user_id}/guilds')
