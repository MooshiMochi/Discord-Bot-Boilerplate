import logging
import os
import sys
from typing import Optional

import yaml
from discord.utils import MISSING


def exit_bot() -> None:
    input("Press enter to continue...")
    exit(1)


class _StdOutFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filters the logging levels that should be written to STDOUT.
        Anything smaller than warning goes to STDOUT, anything else goes to STDERR.
        """
        return record.levelno < logging.ERROR


def setup_logging(
    *,
    level: int = MISSING,
) -> None:
    """
    Sets up logging for the bot.
    This function must only be called once!

    Parameters:
        level: The logging level to use. Defaults to INFO.

    Returns:
        None
    """
    if level is MISSING:
        level = logging.INFO

    # noinspection PyProtectedMember
    from discord.utils import _ColourFormatter as ColourFormatter
    from discord.utils import stream_supports_colour

    OUT = logging.StreamHandler(stream=sys.stdout)
    ERR = logging.StreamHandler(stream=sys.stderr)

    if (
        os.name == "nt" and "PYCHARM_HOSTED" in os.environ
    ):  # this patch is only required for pycharm
        # apply patch for isatty in pycharm being broken
        OUT.stream.isatty = lambda: True
        ERR.stream.isatty = lambda: True

    if isinstance(OUT, logging.StreamHandler) and stream_supports_colour(OUT.stream):
        formatter = ColourFormatter()
    else:
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
        )

    OUT.setFormatter(formatter)
    ERR.setFormatter(formatter)

    OUT.setLevel(level)
    ERR.setLevel(logging.ERROR)

    OUT.addFilter(_StdOutFilter())  # anything error or above goes to stderr

    root = logging.getLogger()
    root.setLevel(level)

    # clear out any existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    root.addHandler(OUT)
    root.addHandler(ERR)


async def ensure_environment(bot, logger) -> None:
    if not os.path.isdir(".git"):
        logger.critical(
            "Bot wasn't installed using Git. Please re-install using the command below:"
        )
        logger.critical(
            "\n     git clone https://github.com/taporsnap37/miasma-public-bot.git\n"
        )
        await bot.close()
        exit_bot()


def load_config(
    logger: logging.Logger, *, auto_exit: bool = True, filepath: str = "config.yml"
) -> Optional[dict]:
    if not os.path.exists(filepath):
        logger.critical(
            "- config.yml file not found. Please follow the instructions listed in the README.md file."
        )
        if auto_exit:
            return exit_bot()

        logger.critical("- Creating a new config.yml file...")
        with open(filepath, "w"):
            pass

    with open(filepath, "r") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.critical(
                "- config.yml file is not a valid YAML file. Please follow the instructions "
                "listed in the README.md file."
            )
            logger.critical("   - Error: " + str(e))
            if auto_exit:
                exit_bot()
            return {}


def silence_loggers(logger_names: list[str]) -> None:
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
