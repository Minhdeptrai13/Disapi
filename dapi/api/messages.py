"""
api/messages.py — Discord Messages API
"""

from __future__ import annotations

import asyncio
import os
import mimetypes
from typing import Any, Dict, List, Optional, Union

from ..http_client import HTTPClient, Route
from ..models.message import Attachment, Message, MessageReference
from ..models.embed import Embed
from ..utils import generate_nonce, split_message
from ..constants import MAX_MESSAGE_LENGTH
from ..exceptions import InvalidArgument


class MessagesAPI:
    """All Discord message-related endpoints.

    Access via ``client.messages.*``.

    Example:
        msg = await client.messages.send("123", "Hello!")
        await client.messages.reply("123", msg.id, "Nice message!")
        await client.messages.delete("123", msg.id)
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    async def send(
        self,
        channel_id: str,
        content: Optional[str] = None,
        *,
        embed: Optional[Union[Dict, Embed]] = None,
        embeds: Optional[List[Union[Dict, Embed]]] = None,
        reply_to: Optional[str] = None,
        tts: bool = False,
        stickers: Optional[List[str]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Any] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        flags: int = 0,
    ) -> Message:
        """Send a message to a channel.

        Args:
            channel_id: Target channel snowflake ID.
            content: Text content (max 2000 chars).
            embed: Single embed to include.
            embeds: Multiple embeds (max 10).
            reply_to: Message ID to reply to.
            tts: Whether to use text-to-speech.
            stickers: Up to 3 sticker IDs to include.
            components: Message component rows.
            files: Multipart file data for attachments.
            nonce: Custom nonce (auto-generated if None).
            allowed_mentions: Mention permission overrides.
            flags: Message flags.

        Returns:
            The created ``Message``.

        Raises:
            BadRequest: If content is invalid.
            Forbidden: If missing SEND_MESSAGES permission.
            InvalidArgument: If no content, embeds, stickers, or files.
        """
        payload: Dict[str, Any] = {"tts": tts}
        if flags:
            payload["flags"] = flags

        if not any((content, embed, embeds, stickers, files, components)):
            raise InvalidArgument("Message", "Cannot send an empty message. Provide content, embed, files, or stickers.")

        if content is not None:
            payload["content"] = content[:MAX_MESSAGE_LENGTH]
        elif embed or embeds or files or stickers:
            # Selfbots sometimes need an explicit empty string content when sending only embeds/attachments
            payload["content"] = ""

        # Resolve embeds
        all_embeds: Optional[List[Dict]] = None
        if embed is not None:
            single = embed.to_dict() if isinstance(embed, Embed) else embed
            all_embeds = [single]
        elif embeds is not None:
            all_embeds = [
                (e.to_dict() if isinstance(e, Embed) else e) for e in embeds[:10]
            ]
        if all_embeds is not None:
            payload["embeds"] = all_embeds

        if reply_to:
            payload["message_reference"] = {
                "message_id": reply_to,
                "fail_if_not_exists": False,
            }

        if stickers:
            payload["sticker_ids"] = stickers[:3]

        if components:
            payload["components"] = components

        if allowed_mentions:
            payload["allowed_mentions"] = allowed_mentions

        payload["nonce"] = nonce if nonce is not None else generate_nonce()

        data = await self._http.request(
            Route("POST", "/channels/{channel_id}/messages", channel_id=channel_id),
            json_payload=payload,
            files=files,
        )
        return Message.from_dict(data)

    async def send_long(
        self,
        channel_id: str,
        content: str,
        delay: float = 0.75,
        **kwargs: Any,
    ) -> List[Message]:
        """Send a long message, automatically splitting into chunks.

        Args:
            channel_id: Target channel ID.
            content: Full content (may exceed 2000 chars).
            delay: Seconds to wait between chunks.
            **kwargs: Extra arguments forwarded to ``send()``.

        Returns:
            List of created ``Message`` objects.
        """
        chunks = split_message(content)
        messages: List[Message] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(delay)
            msg = await self.send(channel_id, content=chunk, **kwargs)
            messages.append(msg)
        return messages

    async def reply(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        *,
        mention_author: bool = True,
        **kwargs: Any,
    ) -> Message:
        """Reply to a specific message.

        Args:
            channel_id: Channel containing the target message.
            message_id: ID of the message to reply to.
            content: Reply text content.
            mention_author: Whether to mention the author.
            **kwargs: Extra arguments forwarded to ``send()``.

        Returns:
            The created reply ``Message``.
        """
        allowed_mentions = kwargs.pop("allowed_mentions", None) or {}
        allowed_mentions["replied_user"] = mention_author

        return await self.send(
            channel_id,
            content=content,
            reply_to=message_id,
            allowed_mentions=allowed_mentions,
            **kwargs,
        )

    async def get(self, channel_id: str, message_id: str) -> Message:
        """Fetch a single message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.

        Returns:
            The ``Message`` object.
        """
        data = await self._http.get(
            f"/channels/{channel_id}/messages/{message_id}"
        )
        return Message.from_dict(data)

    async def get_many(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None,
    ) -> List[Message]:
        """Fetch multiple messages from a channel.

        Args:
            channel_id: Channel ID.
            limit: Number of messages to return (max 100).
            before: Fetch messages before this message ID.
            after: Fetch messages after this message ID.
            around: Fetch messages around this message ID.

        Returns:
            List of ``Message`` objects (newest first by default).
        """
        params: Dict[str, Any] = {"limit": min(max(1, limit), 100)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if around:
            params["around"] = around

        data = await self._http.get(f"/channels/{channel_id}/messages", params=params)
        return [Message.from_dict(m) for m in (data or [])]

    async def edit(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        *,
        embed: Optional[Union[Dict, Embed]] = None,
        embeds: Optional[List[Union[Dict, Embed]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        flags: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Edit an existing message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID to edit (must be your own message).
            content: New text content (pass ``""`` to clear).
            embed: New embed.
            embeds: New embeds.
            components: New components.
            flags: New flags bitmask.
            attachments: Keep specific attachments (pass ``[]`` to remove all).
            allowed_mentions: New allowed mentions.

        Returns:
            The edited ``Message``.
        """
        payload: Dict[str, Any] = {}

        if content is not None:
            payload["content"] = content[:MAX_MESSAGE_LENGTH] if content else ""

        # Resolve embeds
        if embed is not None:
            payload["embeds"] = [embed.to_dict() if isinstance(embed, Embed) else embed]
        elif embeds is not None:
            payload["embeds"] = [
                (e.to_dict() if isinstance(e, Embed) else e) for e in embeds[:10]
            ]

        if components is not None:
            payload["components"] = components
        if flags is not None:
            payload["flags"] = flags
        if attachments is not None:
            payload["attachments"] = attachments
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions

        data = await self._http.request(
            Route("PATCH", "/channels/{channel_id}/messages/{message_id}",
                  channel_id=channel_id, message_id=message_id),
            json_payload=payload,
        )
        return Message.from_dict(data)

    async def delete(
        self,
        channel_id: str,
        message_id: str,
        reason: Optional[str] = None,
    ) -> None:
        """Delete a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            reason: Audit log reason.
        """
        await self._http.request(
            Route("DELETE", "/channels/{channel_id}/messages/{message_id}",
                  channel_id=channel_id, message_id=message_id),
            reason=reason,
        )

    async def bulk_delete(
        self,
        channel_id: str,
        message_ids: List[str],
        reason: Optional[str] = None,
    ) -> None:
        """Bulk-delete 2–100 messages at once.

        Note:
            Messages older than 14 days cannot be bulk-deleted.

        Args:
            channel_id: Channel ID.
            message_ids: List of 2–100 message IDs.
            reason: Audit log reason.

        Raises:
            InvalidArgument: If fewer than 2 or more than 100 IDs provided.
        """
        count = len(message_ids)
        if count < 2 or count > 100:
            raise InvalidArgument("message_ids", "Must provide between 2 and 100 message IDs")

        await self._http.request(
            Route("POST", "/channels/{channel_id}/messages/bulk-delete",
                  channel_id=channel_id),
            json_payload={"messages": message_ids},
            reason=reason,
        )

    async def pin(
        self,
        channel_id: str,
        message_id: str,
        reason: Optional[str] = None,
    ) -> None:
        """Pin a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            reason: Audit log reason.
        """
        await self._http.request(
            Route("PUT", "/channels/{channel_id}/pins/{message_id}",
                  channel_id=channel_id, message_id=message_id),
            reason=reason,
        )

    async def unpin(
        self,
        channel_id: str,
        message_id: str,
        reason: Optional[str] = None,
    ) -> None:
        """Unpin a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            reason: Audit log reason.
        """
        await self._http.request(
            Route("DELETE", "/channels/{channel_id}/pins/{message_id}",
                  channel_id=channel_id, message_id=message_id),
            reason=reason,
        )

    async def get_pins(self, channel_id: str) -> List[Message]:
        """Get all pinned messages in a channel.

        Args:
            channel_id: Channel ID.

        Returns:
            List of pinned ``Message`` objects.
        """
        data = await self._http.get(f"/channels/{channel_id}/pins")
        return [Message.from_dict(m) for m in (data or [])]

    async def trigger_typing(self, channel_id: str) -> None:
        """Start the typing indicator in a channel.

        The indicator lasts ~10 seconds. Call repeatedly to keep it active.

        Args:
            channel_id: Channel ID.
        """
        await self._http.post(f"/channels/{channel_id}/typing")

    async def crosspost(self, channel_id: str, message_id: str) -> Message:
        """Publish a message in an Announcement channel to all followers.

        Args:
            channel_id: Announcement channel ID.
            message_id: Message ID to crosspost.

        Returns:
            The crossposted ``Message``.
        """
        data = await self._http.post(
            f"/channels/{channel_id}/messages/{message_id}/crosspost"
        )
        return Message.from_dict(data)

    async def search_guild(
        self,
        guild_id: str,
        content: Optional[str] = None,
        author_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        has: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> List[Message]:
        """Search for messages in a guild.

        Args:
            guild_id: Guild to search in.
            content: Text to search for.
            author_id: Filter by author user ID.
            channel_id: Filter by channel.
            limit: Max results (max 25).
            offset: Pagination offset.
            has: Filter by attachment type (``'image'``, ``'video'``, etc.).
            before: Message ID cursor.
            after: Message ID cursor.

        Returns:
            List of matching ``Message`` objects.
        """
        params: Dict[str, Any] = {
            "limit": min(limit, 25),
            "offset": offset,
        }
        if content:
            params["content"] = content
        if author_id:
            params["author_id"] = author_id
        if channel_id:
            params["channel_id"] = channel_id
        if has:
            params["has"] = has
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        data = await self._http.get(f"/guilds/{guild_id}/messages/search", params=params)
        messages_data = data.get("messages", []) if isinstance(data, dict) else []
        # Search returns a list of message arrays (context messages)
        result: List[Message] = []
        for group in messages_data:
            if isinstance(group, list):
                result.extend(Message.from_dict(m) for m in group)
            elif isinstance(group, dict):
                result.append(Message.from_dict(group))
        return result

    async def interact_with_slash(
        self,
        application_id: str,
        interaction_id: str,
        interaction_token: str,
        response_type: int = 4,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        ephemeral: bool = False,
    ) -> None:
        """Respond to a slash command interaction.

        Args:
            application_id: Application ID of the bot.
            interaction_id: Interaction ID from the event.
            interaction_token: Interaction token.
            response_type: Interaction callback type (4 = CHANNEL_MESSAGE_WITH_SOURCE).
            content: Response text.
            embeds: Response embeds.
            ephemeral: If True, only the command invoker sees the response.
        """
        data: Dict[str, Any] = {}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if ephemeral:
            data["flags"] = 64  # EPHEMERAL flag

        await self._http.post(
            f"/interactions/{interaction_id}/{interaction_token}/callback",
            json={
                "type": response_type,
                "data": data,
            },
        )
