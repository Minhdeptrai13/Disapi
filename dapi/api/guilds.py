"""Guilds API module."""
from typing import Any, Dict, List, Optional

from ..http_client import HTTPClient
from ..models.guild import Guild, Role
from ..models.user import Member


class GuildsAPI:
    """Guilds API.

    This class provides methods for interacting with Discord's guild endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    async def get(
        self,
        guild_id: str,
        with_counts: bool = True
    ) -> Guild:
        """Get guild by ID.

        Args:
            guild_id: Guild ID.
            with_counts: Include approximate member/presence counts.

        Returns:
            Guild object.
        """
        params = {}
        if with_counts:
            params['with_counts'] = 'true'

        data = await self._http.get(f'/guilds/{guild_id}', params=params)
        return Guild.from_dict(data)

    async def get_preview(self, guild_id: str) -> Dict:
        """Get guild preview (public, no auth needed).

        Args:
            guild_id: Guild ID.

        Returns:
            Guild preview.
        """
        return await self._http.get(f'/guilds/{guild_id}/preview')

    async def get_channels(self, guild_id: str) -> List[Dict]:
        """Get guild channels.

        Args:
            guild_id: Guild ID.

        Returns:
            List of channels.
        """
        return await self._http.get(f'/guilds/{guild_id}/channels')

    async def get_roles(self, guild_id: str) -> List[Role]:
        """Get guild roles.

        Args:
            guild_id: Guild ID.

        Returns:
            List of Roles.
        """
        data = await self._http.get(f'/guilds/{guild_id}/roles')
        return [Role.from_dict(r) for r in data]

    async def get_member(self, guild_id: str, user_id: str) -> Member:
        """Get guild member.

        Args:
            guild_id: Guild ID.
            user_id: User ID.

        Returns:
            Member object.
        """
        data = await self._http.get(f'/guilds/{guild_id}/members/{user_id}')
        return Member.from_dict(data)

    async def get_members(
        self,
        guild_id: str,
        limit: int = 1000,
        after: Optional[str] = None
    ) -> List[Member]:
        """Get guild members.

        Args:
            guild_id: Guild ID.
            limit: Number of members (max 1000).
            after: Get members after this ID.

        Returns:
            List of Members.
        """
        params = {'limit': min(limit, 1000)}
        if after:
            params['after'] = after

        data = await self._http.get(
            f'/guilds/{guild_id}/members',
            params=params
        )
        return [Member.from_dict(m) for m in data]

    async def search_members(
        self,
        guild_id: str,
        query: str,
        limit: int = 1
    ) -> List[Member]:
        """Search guild members by name.

        Args:
            guild_id: Guild ID.
            query: Search query.
            limit: Max results.

        Returns:
            List of matching Members.
        """
        params = {'query': query, 'limit': limit}
        data = await self._http.get(
            f'/guilds/{guild_id}/members/search',
            params=params
        )
        return [Member.from_dict(m) for m in data]

    async def modify_member(
        self,
        guild_id: str,
        user_id: str,
        nick: Optional[str] = None,
        roles: Optional[List[str]] = None,
        mute: Optional[bool] = None,
        deaf: Optional[bool] = None,
        communication_disabled_until: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Member:
        """Modify guild member.

        Args:
            guild_id: Guild ID.
            user_id: User ID.
            nick: New nickname.
            roles: New role IDs.
            mute: Mute state.
            deaf: Deafen state.
            communication_disabled_until: Timeout expiry (ISO timestamp).
            reason: Audit log reason.

        Returns:
            Modified Member.
        """
        payload: Dict[str, Any] = {}
        if nick is not None:
            payload['nick'] = nick
        if roles is not None:
            payload['roles'] = roles
        if mute is not None:
            payload['mute'] = mute
        if deaf is not None:
            payload['deaf'] = deaf
        if communication_disabled_until is not None:
            payload['communication_disabled_until'] = communication_disabled_until

        data = await self._http.patch(
            f'/guilds/{guild_id}/members/{user_id}',
            json=payload,
            reason=reason
        )
        return Member.from_dict(data)

    async def kick(
        self,
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Kick a member from the guild.

        Args:
            guild_id: Guild ID.
            user_id: User ID.
            reason: Audit log reason.
        """
        await self._http.delete(
            f'/guilds/{guild_id}/members/{user_id}',
            reason=reason
        )

    async def ban(
        self,
        guild_id: str,
        user_id: str,
        delete_message_days: int = 0,
        reason: Optional[str] = None
    ) -> None:
        """Ban a user from the guild.

        Args:
            guild_id: Guild ID.
            user_id: User ID.
            delete_message_days: Days of messages to delete (0-7).
            reason: Audit log reason.
        """
        params = {'delete_message_days': delete_message_days}
        await self._http.put(
            f'/guilds/{guild_id}/bans/{user_id}',
            params=params,
            reason=reason
        )

    async def unban(
        self,
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Unban a user from the guild.

        Args:
            guild_id: Guild ID.
            user_id: User ID.
            reason: Audit log reason.
        """
        await self._http.delete(
            f'/guilds/{guild_id}/bans/{user_id}',
            reason=reason
        )

    async def get_bans(
        self,
        guild_id: str,
        limit: int = 1000,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> List[Dict]:
        """Get guild bans.

        Args:
            guild_id: Guild ID.
            limit: Max results.
            before: Before ban ID.
            after: After ban ID.

        Returns:
            List of bans.
        """
        params = {'limit': limit}
        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return await self._http.get(f'/guilds/{guild_id}/bans', params=params)

    async def get_ban(self, guild_id: str, user_id: str) -> Dict:
        """Get a specific ban.

        Args:
            guild_id: Guild ID.
            user_id: User ID.

        Returns:
            Ban info.
        """
        return await self._http.get(f'/guilds/{guild_id}/bans/{user_id}')

    async def get_emojis(self, guild_id: str) -> List[Dict]:
        """Get guild emojis.

        Args:
            guild_id: Guild ID.

        Returns:
            List of emoji dicts.
        """
        data = await self._http.get(f'/guilds/{guild_id}/emojis')
        return data

    async def get_stickers(self, guild_id: str) -> List[Dict]:
        """Get guild stickers.

        Args:
            guild_id: Guild ID.

        Returns:
            List of sticker dicts.
        """
        data = await self._http.get(f'/guilds/{guild_id}/stickers')
        return data

    async def get_prune_count(
        self,
        guild_id: str,
        days: int = 7,
        include_roles: Optional[List[str]] = None
    ) -> int:
        """Get prune count.

        Args:
            guild_id: Guild ID.
            days: Days of inactivity.
            include_roles: Roles to include.

        Returns:
            Number of members that would be pruned.
        """
        params = {'days': days}
        if include_roles:
            params['include_roles'] = ','.join(include_roles)

        data = await self._http.get(f'/guilds/{guild_id}/prune', params=params)
        return data.get('pruned', 0)

    async def get_voice_regions(self, guild_id: str) -> List[Dict]:
        """Get voice regions for guild.

        Args:
            guild_id: Guild ID.

        Returns:
            List of voice regions.
        """
        return await self._http.get(f'/guilds/{guild_id}/regions')

    async def get_invites(self, guild_id: str) -> List[Dict]:
        """Get guild invites.

        Args:
            guild_id: Guild ID.

        Returns:
            List of invites.
        """
        return await self._http.get(f'/guilds/{guild_id}/invites')

    async def get_welcome_screen(self, guild_id: str) -> Dict:
        """Get guild welcome screen.

        Args:
            guild_id: Guild ID.

        Returns:
            Welcome screen info.
        """
        return await self._http.get(f'/guilds/{guild_id}/welcome-screen')

    async def get_vanity_url(self, guild_id: str) -> Dict:
        """Get vanity URL.

        Args:
            guild_id: Guild ID.

        Returns:
            Vanity URL info.
        """
        return await self._http.get(f'/guilds/{guild_id}/vanity-url')

    async def get_audit_log(
        self,
        guild_id: str,
        user_id: Optional[str] = None,
        action_type: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        limit: int = 50
    ) -> Dict:
        """Get guild audit log.

        Args:
            guild_id: Guild ID.
            user_id: Filter by user.
            action_type: Filter by action type.
            before: Before entry ID.
            after: After entry ID.
            limit: Max entries.

        Returns:
            Audit log data.
        """
        params = {'limit': limit}
        if user_id:
            params['user_id'] = user_id
        if action_type:
            params['action_type'] = action_type
        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return await self._http.get(f'/guilds/{guild_id}/audit-logs', params=params)

    async def leave(self, guild_id: str) -> None:
        """Leave the guild.

        Args:
            guild_id: Guild ID.
        """
        await self._http.delete(f'/users/@me/guilds/{guild_id}')
