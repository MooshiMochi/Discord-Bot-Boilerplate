from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional, Union

if TYPE_CHECKING:
    from ..core.client import MiasmaClient

import traceback as tb

import discord
from discord import Embed
from discord.ext import commands
from discord.ui import View


class BaseView(View):
    def __init__(
        self,
        bot: MiasmaClient,
        interaction: discord.Interaction | commands.Context = None,
        timeout: float | None = 60.0,
    ):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.interaction_or_ctx: discord.Interaction | commands.Context = interaction
        self.message: discord.Message | None = None

    async def on_timeout(self) -> None:
        if self.message is not None:
            await self.message.edit(
                view=None,
                embed=Embed(
                    color=discord.Color.red(),
                    title="Timed out",
                    description="No changes were made.",
                ),
            )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Button,
        /,
    ) -> None:
        traceback = "".join(
            tb.format_exception(type(error), error, error.__traceback__)
        )
        self.bot.logger.error(traceback)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"An error occurred: ```py\n{traceback[-1800:]}```", ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"An error occurred: ```py\n{traceback[-1800:]}```", ephemeral=True
            )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if isinstance(self.interaction_or_ctx, discord.Interaction):
            author = self.interaction_or_ctx.user
        else:
            author = self.interaction_or_ctx.author

        if author.id == interaction.user.id:
            return True
        else:
            embed = Embed(title=f"🚫 You cannot use this menu!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False


class ConfirmView(BaseView):
    def __init__(
        self,
        bot: MiasmaClient,
        interaction_or_ctx: discord.Interaction | commands.Context,
    ):
        super().__init__(bot, interaction_or_ctx)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _):
        await interaction.response.defer(ephemeral=True, thinking=False)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.defer(ephemeral=True, thinking=False)
        self.value = False
        self.stop()


class PaginatorView(discord.ui.View):
    def __init__(
        self,
        items: list[Union[str, int, Embed]] = None,
        interaction: Union[discord.Interaction, commands.Context] = None,
        timeout: float = 3 * 3600,  # 3 hours,
        *args,
        **kwargs,
    ) -> None:
        self.items = items
        self.interaction: discord.Interaction = interaction
        self.page: int = 0
        self.message: Optional[discord.Message] = None

        if not self.items and not self.interaction:
            raise AttributeError(
                "A list of items of type 'Union[str, int, Embed]' was not provided to iterate through as well as the "
                "interaction."
            )

        elif not items:
            raise AttributeError(
                "A list of items of type 'Union[str, int, Embed]' was not provided to iterate through."
            )

        elif not interaction:
            raise AttributeError("The command interaction was not provided.")

        if not isinstance(items, Iterable):
            raise AttributeError(
                "An iterable containing items of type 'Union[str, int, Embed]' classes is required."
            )

        elif not all(isinstance(item, (str, int, Embed)) for item in items):
            raise AttributeError(
                "All items within the iterable must be of type 'str', 'int' or 'Embed'."
            )

        super().__init__(timeout=timeout)
        self.items = list(self.items)
        if (
            len(self.items) == 1
        ):  # no need to paginate if there's only one item to display
            for _child in self.children:
                if _child.row == 0:
                    self.remove_item(_child)

    def __get_response_kwargs(self):
        if isinstance(self.items[self.page], Embed):
            return {"embed": self.items[self.page]}
        else:
            return {"content": self.items[self.page]}

    @discord.ui.button(label=f"⏮️", style=discord.ButtonStyle.blurple, row=0)
    async def _first_page(self, interaction: discord.Interaction, _):
        self.page = 0
        await interaction.response.edit_message(**self.__get_response_kwargs())

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple, row=0)
    async def back(self, interaction: discord.Interaction, _):
        self.page -= 1
        if self.page == -1:
            self.page = len(self.items) - 1
        await interaction.response.edit_message(**self.__get_response_kwargs())

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.red, row=0)
    async def _stop(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple, row=0)
    async def forward(self, interaction: discord.Interaction, _):
        self.page += 1
        if self.page == len(self.items):
            self.page = 0
        await interaction.response.edit_message(**self.__get_response_kwargs())

    @discord.ui.button(label=f"⏭️", style=discord.ButtonStyle.blurple, row=0)
    async def _last_page(self, interaction: discord.Interaction, _):
        self.page = len(self.items) - 1
        await interaction.response.edit_message(**self.__get_response_kwargs())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if isinstance(self.interaction, discord.Interaction):
            author = self.interaction.user
        else:
            author = self.interaction.author

        if author.id == interaction.user.id:
            return True
        else:
            embed = Embed(
                bot=interaction.client,
                title=f"🚫 You cannot use this menu!",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        if self.message is not None:
            await self.message.edit(view=None)
        self.stop()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item
    ) -> None:
        if isinstance(error, TimeoutError):
            pass
        else:
            traceback = "".join(
                tb.format_exception(type(error), error, error.__traceback__)
            )
            em = Embed(
                bot=interaction.client,
                title=f"🚫 An unknown error occurred!",
                description=f"{traceback[-2000:]}",
                color=0xFF0000,
            )
            interaction.client.logger.error(traceback)

            if interaction.response.is_done():
                await interaction.followup.send(embed=em, ephemeral=True)
            else:
                await interaction.response.send_message(embed=em, ephemeral=True)
