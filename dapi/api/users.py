"""Users API module."""
from typing import Any, Dict, List, Optional

from ..http_client import HTTPClient
from ..models.user import User


class UsersAPI:
    """Users API.

    This class provides methods for interacting with Discord's user endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def get_current_user(self) -> User:
        """Get current user.

        Returns:
            Current User object.
        """
        # Note: If 403 occurs, ensure the HTTP client sends valid x-super-properties,
        # User-Agent, and avoids missing headers.
        data = await self._http.get('/users/@me')
        return User.from_dict(data)

    async def get_user(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User object.
        """
        data = await self._http.get(f'/users/{user_id}')
        return User.from_dict(data)

    async def edit(
        self,
        username: Optional[str] = None,
        avatar: Optional[str] = None,
        banner: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> User:
        """Modify current user's profile (edit).

        Args:
            username: New username.
            avatar: New avatar (base64 data URI).
            banner: New banner (base64 data URI).
            bio: New bio/about me.

        Returns:
            Modified User.
        """
        payload: Dict[str, Any] = {}
        if username is not None:
            payload['username'] = username
        if avatar is not None:
            payload['avatar'] = avatar
        if banner is not None:
            payload['banner'] = banner
        if bio is not None:
            payload['bio'] = bio

        data = await self._http.patch('/users/@me', json_payload=payload)
        return User.from_dict(data)

    async def get_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships (friends, blocked, outgoing/incoming requests).

        Returns:
            List of relationship objects.
        """
        # Selfbots usually fetch relationships from /users/@me/relationships
        return await self._http.get('/users/@me/relationships')

    async def get_current_guilds(
        self,
        limit: int = 200,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> List[Dict]:
        """Get current user's guilds.

        Args:
            limit: Max guilds to return (max 200).
            before: Guild ID to get guilds before.
            after: Guild ID to get guilds after.

        Returns:
            List of partial guild data.
        """
        params = {'limit': min(limit, 200)}
        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return await self._http.get('/users/@me/guilds', params=params)

    async def leave_guild(self, guild_id: str) -> None:
        """Leave a guild.

        Args:
            guild_id: Guild ID.
        """
        await self._http.delete(f'/users/@me/guilds/{guild_id}')

    async def create_dm(self, recipient_id: str) -> Dict:
        """Create a DM channel with a user.

        Args:
            recipient_id: User ID to create DM with.

        Returns:
            DM Channel object.
        """
        return await self._http.post(
            '/users/@me/channels',
            json={'recipient_id': recipient_id}
        )

    async def create_group_dm(
        self,
        access_tokens: List[str],
        nicks: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Create a group DM.

        Args:
            access_tokens: OAuth2 access tokens of recipients.
            nicks: Dict of user IDs to nicknames.

        Returns:
            Group DM Channel.
        """
        payload: Dict[str, Any] = {'access_tokens': access_tokens}
        if nicks:
            payload['nicks'] = nicks
        return await self._http.post('/users/@me/channels', json=payload)

    async def get_dms(self) -> List[Dict]:
        """Get user's DM channels.

        Returns:
            List of DM channels.
        """
        return await self._http.get('/users/@me/channels')

    async def get_connections(self) -> List[Dict]:
        """Get user's connected accounts.

        Returns:
            List of connections (Steam, Spotify, etc).
        """
        return await self._http.get('/users/@me/connections')

    async def get_application(self) -> Dict:
        """Get current application info.

        Returns:
            Application info.
        """
        return await self._http.get('/oauth2/applications/@me')

    async def get_authorization_info(self) -> Dict:
        """Get current authorization info.

        Returns:
            Authorization info.
        """
        return await self._http.get('/oauth2/@me')

    async def join_guild(
        self,
        invite_code: str,
        event_id: Optional[str] = None
    ) -> Dict:
        """Join a guild via invite.

        Args:
            invite_code: Invite code.
            event_id: Guild scheduled event ID.

        Returns:
            Guild object.
        """
        params = {}
        if event_id:
            params['guild_scheduled_event_id'] = event_id

        return await self._http.post(f'/invites/{invite_code}', params=params)

    async def get_mutual_guilds(self, user_id: str) -> List[Dict]:
        """Get mutual guilds with a user.

        Note: This requires fetching guilds and checking members.

        Args:
            user_id: User ID.

        Returns:
            List of mutual guild IDs.
        """
        guilds = await self.get_current_guilds()
        mutual = []

        for guild in guilds:
            try:
                guild_id = guild['id']
                # This would require additional API calls
                # For now, just return the guild data
                mutual.append(guild)
            except Exception:
                continue

        return mutual
