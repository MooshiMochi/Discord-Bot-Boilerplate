from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.client import MyClient

import asyncio
import logging

import asyncpg
import discord
from discord.ext import commands


class Database(commands.Cog):
    """
    fuzzy matching postgresql query:

    SELECT * FROM {self.table} WHERE $1 % ANY(STRING_TO_ARRAY(name,'')) LIMIT 25

    When do you use fuzzy matching:
        I want shit that matches this but not exactly

    normal:
        if you want an exact thing.
    """

    def __init__(self, bot: MyClient):
        self.bot: MyClient = bot
        self.logger = logging.getLogger("database")
        self.poo: asyncpg.pool.Pool | None = None

    async def get_pool(self):
        kwargs = {
            "host": self.bot.config["database"]["ip"],
            "port": self.bot.config["database"]["port"],
            "user": self.bot.config["database"]["username"],
            "password": self.bot.config["database"]["password"],
            "min_size": 3,
            "max_size": 10,
            "command_timeout": 60,
            "loop": asyncio.get_event_loop(),
        }
        return await asyncpg.create_pool(**kwargs)

    async def cog_load(self):
        self.logger.info("Attempting to establish a database connection...")
        self.pool = await self.get_pool()
        self.logger.info("Database connection established successfully.")

    async def cog_unload(self):
        await self.pool.close()
        self.logger.info("Database connection closed.")


async def setup(bot: MyClient) -> None:
    if bot.debug and bot.test_guild_ids:
        await bot.add_cog(
            Database(bot), guilds=[discord.Object(id=x) for x in bot.test_guild_ids]
        )
    else:
        await bot.add_cog(Database(bot))
