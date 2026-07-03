"""
dapi/ext/commands.py — Lightweight Command Framework
=====================================================

Provides a prefix-based command framework built on top of the Dapi Client.

Example:
    from dapi import Client
    from dapi.ext import commands

    bot = commands.Bot(command_prefix="!", token="YOUR_TOKEN")

    @bot.command(name="ping")
    async def ping(ctx: commands.Context):
        await ctx.reply("Pong!")

    bot.run()
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar, Union

from ..client import Client, ClientOptions
from ..models.message import Message
from ..models.user import User
from ..models.channel import Channel
from ..models.embed import Embed

logger = logging.getLogger("dapi.ext.commands")


class Context:
    """Represents the context in which a command is being invoked.
    
    discord.py-style Context with full method support.
    
    Attributes:
        bot (Client): The bot/client instance.
        message (Message): The message that triggered the command.
        author (User): The author of the message.
        channel_id (str): The ID of the channel.
        guild_id (Optional[str]): The ID of the guild (if any).
        command (Command): The command that was triggered.
        args (List[str]): List of arguments passed to the command.
        prefix (str): The prefix used to invoke the command.
        invoked_with (str): The command name that was invoked.
        invoked_subcommand (Optional[str]): The subcommand that was invoked.
    """

    def __init__(
        self,
        bot: Client,
        message: Message,
        command: "Command",
        args: List[str],
        prefix: str = "!",
        invoked_with: Optional[str] = None,
    ) -> None:
        self.bot = bot
        self.message = message
        self.author = message.author
        self.channel_id = message.channel_id
        self.guild_id = message.guild_id
        self.command = command
        self.args = args
        self.prefix = prefix
        self.invoked_with = invoked_with or command.name
        self.invoked_subcommand: Optional[str] = None
        self._channel: Optional[Channel] = None

    @property
    def channel(self) -> Channel:
        """Get the channel object."""
        if self._channel is None:
            # For simplicity, create a minimal channel object
            from ..models.channel import Channel
            self._channel = Channel(
                id=self.channel_id,
                type=0 if self.guild_id else 1,  # 0=guild text, 1=dm
                guild_id=self.guild_id,
                name="unknown",
            )
        return self._channel

    @property
    def guild(self) -> Optional[Any]:
        """Get the guild object (if in a guild)."""
        if self.guild_id:
            return self.bot.get_guild(self.guild_id)
        return None

    @property
    def me(self) -> Optional[User]:
        """Get the bot's user object."""
        return self.bot.user

    @property
    def voice_client(self) -> Optional[Any]:
        """Get the voice client (not implemented for selfbots)."""
        return None

    async def send(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        """Send a message to the same channel.
        
        Args:
            content: Message content.
            **kwargs: Additional arguments (embed, tts, etc.)
            
        Returns:
            The created Message.
        """
        return await self.bot.messages.send(self.channel_id, content=content, **kwargs)

    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        """Reply to the message that triggered the command.
        
        Args:
            content: Reply content.
            **kwargs: Additional arguments.
            
        Returns:
            The created reply Message.
        """
        return await self.bot.messages.reply(
            self.channel_id,
            self.message.id,
            content=content,
            **kwargs
        )

    async def edit(self, **kwargs: Any) -> Message:
        """Edit the message that triggered the command.
        
        Args:
            **kwargs: Fields to edit (content, embed, etc.)
            
        Returns:
            The edited Message.
        """
        return await self.bot.messages.edit(
            self.channel_id,
            self.message.id,
            **kwargs
        )

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """Delete the message that triggered the command.
        
        Args:
            delay: Seconds to wait before deleting.
        """
        if delay:
            await asyncio.sleep(delay)
        await self.bot.messages.delete(self.channel_id, self.message.id)

    async def trigger_typing(self) -> None:
        """Trigger the typing indicator in the channel."""
        await self.bot.messages.trigger_typing(self.channel_id)

    def typing(self) -> Any:
        """Returns a context manager for typing.
        
        Not implemented for selfbots.
        """
        class TypingContext:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
        return TypingContext()

    async def fetch_message(self, message_id: str) -> Message:
        """Fetch a message from the channel.
        
        Args:
            message_id: Message ID to fetch.
            
        Returns:
            The Message.
        """
        return await self.bot.messages.get(self.channel_id, message_id)

    async def history(
        self,
        *,
        limit: int = 100,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None,
    ) -> List[Message]:
        """Get message history from the channel.
        
        Args:
            limit: Number of messages to fetch.
            before: Message ID to fetch before.
            after: Message ID to fetch after.
            around: Message ID to fetch around.
            
        Returns:
            List of Messages.
        """
        return await self.bot.messages.get_many(
            self.channel_id,
            limit=limit,
            before=before,
            after=after,
            around=around,
        )

    async def pin(self) -> None:
        """Pin the message that triggered the command."""
        await self.bot.messages.pin(self.channel_id, self.message.id)

    async def unpin(self) -> None:
        """Unpin the message that triggered the command."""
        await self.bot.messages.unpin(self.channel_id, self.message.id)

    async def add_reaction(self, emoji: str) -> None:
        """Add a reaction to the message.
        
        Args:
            emoji: Emoji to add (unicode or custom format).
        """
        await self.bot.reactions.add(self.channel_id, self.message.id, emoji)

    async def remove_reaction(self, emoji: str, user_id: Optional[str] = None) -> None:
        """Remove a reaction from the message.
        
        Args:
            emoji: Emoji to remove.
            user_id: User ID whose reaction to remove (None for own).
        """
        target_user = user_id or self.author.id
        await self.bot.reactions.remove(self.channel_id, self.message.id, emoji, target_user)

    async def clear_reactions(self) -> None:
        """Clear all reactions from the message."""
        await self.bot.reactions.clear_all(self.channel_id, self.message.id)
    
    async def fetch_channel(self) -> Channel:
        """Fetch the channel object from API.
        
        Returns:
            The Channel object.
        """
        return await self.bot.get_channel(self.channel_id)
    
    async def fetch_guild(self) -> Optional[Any]:
        """Fetch the guild object from API (if in a guild).
        
        Returns:
            The Guild object or None if not in a guild.
        """
        if self.guild_id:
            return await self.bot.get_guild(self.guild_id)
        return None
    
    async def fetch_author(self) -> User:
        """Fetch the author's user object from API.
        
        Returns:
            The User object.
        """
        return await self.bot.get_user(self.author.id)
    
    @property
    def voice(self) -> Optional[Any]:
        """Get the voice state (not implemented for selfbots)."""
        return None


class Command:
    """Represents a command.
    
    Attributes:
        name (str): The name of the command.
        callback (Callable): The coroutine to execute when invoked.
    """
    def __init__(self, name: str, callback: Callable[..., Coroutine[Any, Any, None]]):
        self.name = name
        self.callback = callback

    async def invoke(self, ctx: Context) -> None:
        try:
            await self.callback(ctx)
        except Exception as e:
            logger.error(f"Error invoking command '{self.name}': {e}")


class Bot(Client):
    """A bot client implementing a prefix command framework.
    
    Inherits from the standard Dapi `Client`.
    
    Args:
        command_prefix (str | List[str]): The prefix(es) used to identify commands.
        token (str): Discord user token.
        options (ClientOptions): ClientOptions for configuration.
    """

    def __init__(
        self,
        command_prefix: Union[str, List[str]],
        token: str,
        options: Optional[ClientOptions] = None
    ) -> None:
        super().__init__(token, options)
        self.command_prefix = [command_prefix] if isinstance(command_prefix, str) else command_prefix
        self.commands: Dict[str, Command] = {}
        
        # Register the internal message listener
        self.on("MESSAGE_CREATE")(self._on_message_create)

    def command(self, name: Optional[str] = None) -> Callable:
        """Decorator to register a command.
        
        Args:
            name: Optional command name. Defaults to the function name.
        """
        def decorator(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable:
            cmd_name = name or func.__name__
            cmd = Command(cmd_name, func)
            self.commands[cmd_name] = cmd
            logger.debug(f"Registered command: {cmd_name}")
            return func
        return decorator

    async def _on_message_create(self, data: Dict[str, Any]) -> None:
        """Internal handler to process commands."""
        # Simple safeguard against self-bots looping if they reply to themselves?
        # Typically selfbots do respond to their own messages, but be careful.
        content: str = data.get("content", "")
        if not content:
            return

        # Check for prefix
        prefix_matched = None
        for prefix in self.command_prefix:
            if content.startswith(prefix):
                prefix_matched = prefix
                break

        if not prefix_matched:
            return

        # Parse command and args
        # e.g., "!ping arg1 arg2" -> "!ping", "arg1 arg2"
        parts = content[len(prefix_matched):].strip().split()
        if not parts:
            return

        cmd_name = parts[0].lower()
        if cmd_name in self.commands:
            message = Message.from_dict(data)
            command = self.commands[cmd_name]
            ctx = Context(self, message, command, parts[1:])
            
            # Fire command async
            asyncio.create_task(command.invoke(ctx))

    def run(self) -> None:
        """Helper to run the bot blocking the main thread."""
        async def runner():
            async with self:
                await self.login()
                if self.gateway:
                    await self.gateway.connect()
                    # Keep alive
                    while True:
                        await asyncio.sleep(3600)
        
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            logger.info("Bot shutting down...")
