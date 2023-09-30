import asyncio
import logging
import os
import sys

from aiohttp import ClientConnectorError
from discord import Intents
from discord.errors import LoginFailure

from src.core.client import MiasmaClient
from src.utils.startup import (
    ensure_environment,
    exit_bot,
    load_config,
    setup_logging,
    silence_loggers,
)


async def load_extensions(client: MiasmaClient, extensions: list[str]) -> None:
    for extension in extensions:
        await client.load_extension(extension)


def ensure_logs() -> None:
    if not os.path.exists("logs"):
        os.mkdir("logs")
    if not os.path.exists("logs/error.log"):
        with open("logs/error.log", "w") as f:
            f.write("")


async def main():
    _logger = logging.getLogger("main")
    config = load_config(_logger)
    if config and config.get("debug") is True:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)

    _logger.info("Starting bot...")

    ensure_logs()

    silence_loggers(
        ["discord.client", "discord.gateway", "discord.http", "discord.state"]
    )

    intents = Intents(Intents.default().value, **config["privileged-intents"])
    client = MiasmaClient(config["prefix"], intents)
    client.load_config(config)

    await ensure_environment(client, _logger)

    async with client:
        await load_extensions(client, config["extensions"])
        try:
            await client.start(config["token"])
        except LoginFailure as e:
            _logger.critical(f"{e}")
            _logger.critical(
                "    - Please run the setup.bat file if you're on "
                "windows or the setup.sh file if you're on linux/macOS."
            )
            await client.close()
            exit_bot()
        except ClientConnectorError as e:
            if e.strerror == "getaddrinfo failed":
                _logger.critical(
                    "You are offline! Please connect to a network and try again!"
                )


if __name__ == "__main__":
    try:
        if os.name == "nt" and sys.version_info >= (3, 8):
            import tracemalloc

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            tracemalloc.start()

        asyncio.run(main())
    except KeyboardInterrupt:
        exit(1)
