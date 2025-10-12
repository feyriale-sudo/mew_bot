# 🎀────────────────────────────────────────────
#    🌸 Toggle Command Group 🌸
# ─────────────────────────────────────────────
from typing import Literal, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from utils.group_func.toggle import *


# 🎀────────────────────────────────────────────
#           🌸 MissingPokemon Cog Setup 🌸
# ─────────────────────────────────────────────
class ToggleGroupCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎀────────────────────────────────────────────
    #           🌸 Slash Command Group 🌸
    # 🎀────────────────────────────────────────────
    toggle_group = app_commands.Group(
        name="toggle", description="Commands related to toggling settings"
    )

    # 🎀────────────────────────────────────────────
    #          🌸 /toggle timers 🌸
    # 🎀────────────────────────────────────────────
    @toggle_group.command(
        name="timers", description="Toggle Pokémon, fishing, battle, catchbot, and quest timers"
    )
    async def toggle_timers(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "toggle timers"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=timer_settings_func,
        )
    # 🎀────────────────────────────────────────────
    #          🌸 /toggle utilities 🌸
    # 🎀────────────────────────────────────────────
    @toggle_group.command(
        name="utilities",
        description="Toggle utility settings like fish rarity display",
    )
    async def toggle_utilities(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "toggle utilities"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=utility_settings_func,
        )


# 🎀────────────────────────────────────────────
#           🌸 Cog Setup Function 🌸
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ToggleGroupCommand(bot)
    await bot.add_cog(cog)
