import io
import logging
import os
from typing import Optional, Union

import aiohttp
import discord
from discord import Intents
from discord.ext import commands

from ..utils.static import Emotes
from .database import Database


class MyClient(commands.Bot):
    # noinspection PyTypeChecker
    def __init__(
        self, prefix: str = "!", intents: Intents = Intents.default(), *args, **kwargs
    ):
        # noinspection PyTypeChecker
        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix or "!"),
            intents=intents,
            *args,
            **kwargs,
        )
        self._config = None
        self.test_guild_ids = None
        self.db: Database = None
        self._logger: logging.Logger = logging.getLogger("bot")

        # Placeholder values. These are set in .setup_hook() below
        self._session: aiohttp.ClientSession = None

        self.log_channel_id: Optional[int] = None
        self._debug_mode: bool = False

    async def setup_hook(self):
        self.db = Database(self)  # must be initialized after config is initialized
        self.loop.create_task(self.update_restart_message())

    async def update_restart_message(self):
        await self.wait_until_ready()

        if os.path.exists("logs/restart.txt"):
            with open("logs/restart.txt", "r") as f:
                contents = f.read()
                if not contents:
                    return
                channel_id, msg_id = contents.split("/")[5:]

            with open("logs/restart.txt", "w") as f:  # clear the file
                f.write("")
            channel = self.get_channel(int(channel_id))
            if channel is None:
                return
            try:
                msg = await channel.fetch_message(int(msg_id))
            except discord.NotFound:
                return
            if msg is None:
                return
            em = msg.embeds[0]
            em.description = f"{Emotes.success} `Bot is now online.`"
            return await msg.edit(embed=em)

    def load_config(self, config: dict):
        self.owner_ids = config["constants"].get("owner-ids", [self.owner_id])
        self.test_guild_ids = config["constants"].get("test-guild-ids")
        self.log_channel_id: int = config["constants"].get("log-channel-id")
        self._debug_mode: bool = config.get("debug", False)

        self._config: dict = config

    async def on_ready(self):
        self._logger.info(f"{self.user.name}#{self.user.discriminator} is ready!")

    async def close(self):
        await self._session.close() if self._session else None
        await super().close()

    async def log_to_discord(self, content: Union[str, None] = None, **kwargs) -> None:
        """Log a message to a discord log channel."""
        if not self.is_ready():
            await self.wait_until_ready()

        if not content and not kwargs:
            return

        channel = self.get_channel(self.log_channel_id)

        if not channel:
            return
        try:
            if content and len(content) > 2000:
                # try to send it as a file
                buffer = io.BytesIO(content.encode("utf-8"))
                file = discord.File(fp=buffer, filename="log.py")
                if kwargs.get("file") is None:
                    kwargs["file"] = file
                    content = None
                else:
                    files_kwarg = kwargs.get("files")
                    if files_kwarg is None:
                        kwargs["files"] = [file]
                        content = None
                    elif len(files_kwarg) < 10:
                        kwargs["files"].append(file)
                        content = None
                    else:
                        content = "..." + content[-1997:]
            await channel.send(content, **kwargs)
        except Exception as e:
            self._logger.error(f"Error while logging: {e}")

    async def on_message(self, message: discord.Message, /) -> None:
        await self.process_commands(message)

    @property
    def debug(self):
        return self._debug_mode

    @property
    def session(self):
        return self._session

    @property
    def logger(self):
        return self._logger

    @property
    def config(self):
        return self._config
