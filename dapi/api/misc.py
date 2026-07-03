"""Miscellaneous API module."""
from typing import Any, Dict, List, Optional

from ..http_client import HTTPClient


class MiscAPI:
    """Miscellaneous API.

    This class provides methods for various Discord endpoints.
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    # Invites

    async def get_invite(
        self,
        invite_code: str,
        with_counts: bool = True,
        with_expiration: bool = True,
        guild_scheduled_event_id: Optional[str] = None
    ) -> Dict:
        """Get invite info.

        Args:
            invite_code: Invite code.
            with_counts: Include member counts.
            with_expiration: Include expiration info.
            guild_scheduled_event_id: Event ID.

        Returns:
            Invite object.
        """
        params = {}
        if with_counts:
            params['with_counts'] = 'true'
        if with_expiration:
            params['with_expiration'] = 'true'
        if guild_scheduled_event_id:
            params['guild_scheduled_event_id'] = guild_scheduled_event_id

        return await self._http.get(f'/invites/{invite_code}', params=params)

    async def delete_invite(self, invite_code: str) -> Dict:
        """Delete an invite.

        Args:
            invite_code: Invite code.

        Returns:
            Deleted invite.
        """
        return await self._http.delete(f'/invites/{invite_code}')

    # Billing/Nitro

    async def get_billing_subscriptions(self) -> List[Dict]:
        """Get billing subscriptions.

        Returns:
            List of subscriptions.
        """
        return await self._http.get('/users/@me/billing/subscriptions')

    async def get_billing_history(self) -> List[Dict]:
        """Get billing history.

        Returns:
            List of billing records.
        """
        return await self._http.get('/users/@me/billing/payments')

    async def get_premium_codes(self) -> List[Dict]:
        """Get premium gift codes.

        Returns:
            List of gift codes.
        """
        return await self._http.get('/users/@me/billing/codes')

    async def redeem_gift_code(
        self,
        code: str,
        channel_id: Optional[str] = None
    ) -> Dict:
        """Redeem a Nitro gift code.

        Args:
            code: Gift code.
            channel_id: Optional channel ID.

        Returns:
            Redemption result.
        """
        payload: Dict[str, Any] = {
            'channel_id': channel_id,
            'payment_source_id': None,
        }
        return await self._http.post(
            f'/entitlements/gift-codes/{code}/redeem',
            json=payload
        )

    async def get_entitlements(self) -> List[Dict]:
        """Get user entitlements.

        Returns:
            List of entitlements.
        """
        return await self._http.get('/users/@me/entitlements')

    # Voice/Stage

    async def get_voice_regions(self) -> List[Dict]:
        """Get available voice regions.

        Returns:
            List of voice regions.
        """
        return await self._http.get('/voice/regions')

    async def create_stage_instance(
        self,
        channel_id: str,
        topic: str,
        privacy_level: int = 1
    ) -> Dict:
        """Create a stage instance.

        Args:
            channel_id: Stage channel ID.
            topic: Stage topic.
            privacy_level: Privacy level (1=guild only).

        Returns:
            Stage instance.
        """
        return await self._http.post('/stage-instances', json={
            'channel_id': channel_id,
            'topic': topic,
            'privacy_level': privacy_level,
        })

    async def get_stage_instance(self, channel_id: str) -> Dict:
        """Get stage instance.

        Args:
            channel_id: Stage channel ID.

        Returns:
            Stage instance.
        """
        return await self._http.get(f'/stage-instances/{channel_id}')

    async def update_stage_instance(
        self,
        channel_id: str,
        topic: Optional[str] = None,
        privacy_level: Optional[int] = None
    ) -> Dict:
        """Update stage instance.

        Args:
            channel_id: Stage channel ID.
            topic: New topic.
            privacy_level: New privacy level.

        Returns:
            Updated stage instance.
        """
        payload: Dict[str, Any] = {}
        if topic:
            payload['topic'] = topic
        if privacy_level:
            payload['privacy_level'] = privacy_level
        return await self._http.patch(f'/stage-instances/{channel_id}', json=payload)

    async def delete_stage_instance(self, channel_id: str) -> None:
        """Delete stage instance.

        Args:
            channel_id: Stage channel ID.
        """
        await self._http.delete(f'/stage-instances/{channel_id}')

    # Guild Scheduled Events

    async def get_guild_events(self, guild_id: str) -> List[Dict]:
        """Get guild scheduled events.

        Args:
            guild_id: Guild ID.

        Returns:
            List of events.
        """
        return await self._http.get(f'/guilds/{guild_id}/scheduled-events')

    async def get_event(
        self,
        guild_id: str,
        event_id: str,
        with_user_count: bool = False
    ) -> Dict:
        """Get a guild event.

        Args:
            guild_id: Guild ID.
            event_id: Event ID.
            with_user_count: Include user count.

        Returns:
            Event object.
        """
        params = {}
        if with_user_count:
            params['with_user_count'] = 'true'

        return await self._http.get(
            f'/guilds/{guild_id}/scheduled-events/{event_id}',
            params=params
        )

    async def get_event_users(
        self,
        guild_id: str,
        event_id: str,
        limit: int = 100,
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> List[Dict]:
        """Get event participants.

        Args:
            guild_id: Guild ID.
            event_id: Event ID.
            limit: Max users.
            before: Before ID.
            after: After ID.

        Returns:
            List of users.
        """
        params = {'limit': limit}
        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return await self._http.get(
            f'/guilds/{guild_id}/scheduled-events/{event_id}/users',
            params=params
        )

    # Application Commands

    async def get_guild_commands(
        self,
        application_id: str,
        guild_id: str
    ) -> List[Dict]:
        """Get application commands for guild.

        Args:
            application_id: Application ID.
            guild_id: Guild ID.

        Returns:
            List of commands.
        """
        return await self._http.get(
            f'/applications/{application_id}/guilds/{guild_id}/commands'
        )

    # Sticker Packs

    async def get_sticker_packs(self) -> List[Dict]:
        """Get nitro sticker packs.

        Returns:
            List of sticker packs.
        """
        data = await self._http.get('/sticker-packs')
        return data.get('sticker_packs', [])

    # Phone/Email verification

    async def verify_phone(
        self,
        phone: str,
        code: str
    ) -> Dict:
        """Verify phone number.

        Args:
            phone: Phone number.
            code: Verification code.

        Returns:
            Verification result.
        """
        return await self._http.post('/users/@me/phone/verify', json={
            'phone': phone,
            'code': code,
        })

    async def verify_email(
        self,
        token: str
    ) -> Dict:
        """Verify email.

        Args:
            token: Verification token.

        Returns:
            Verification result.
        """
        return await self._http.post('/users/@me/email/verify', json={
            'token': token,
        })

    # User connections

    async def authorize_connection(
        self,
        type: str,
        two_way_link_type: int = 1,
        two_way_link_user_code: Optional[str] = None
    ) -> Dict:
        """Authorize a connection (e.g., Xbox, PlayStation).

        Args:
            type: Connection type.
            two_way_link_type: Link type.
            two_way_link_user_code: User code.

        Returns:
            Authorization URL or result.
        """
        payload: Dict[str, Any] = {
            'type': type,
            'two_way_link_type': two_way_link_type,
        }
        if two_way_link_user_code:
            payload['two_way_link_user_code'] = two_way_link_user_code

        return await self._http.post('/users/@me/connections', json=payload)

    async def get_connection_url(
        self,
        connection_type: str,
        connection_id: str
    ) -> Dict:
        """Get connection URL.

        Args:
            connection_type: Connection type.
            connection_id: Connection ID.

        Returns:
            Connection URL info.
        """
        return await self._http.get(
            f'/users/@me/connections/{connection_type}/{connection_id}'
        )
