# 🎀────────────────────────────────────────────
#    🌸 Missing Pokemon Command Group 🌸
# ─────────────────────────────────────────────
from typing import Literal, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from utils.group_func.missing_pokemon import *
from utils.db.missing_pokemon_db_func import user_missing_pokemon_autocomplete

# 🎀────────────────────────────────────────────
#           🌸 MissingPokemon Cog Setup 🌸
# ─────────────────────────────────────────────
class MissingPokemon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎀────────────────────────────────────────────
    #           🌸 Slash Command Group 🌸
    # 🎀────────────────────────────────────────────
    missing_pokemon_group = app_commands.Group(
        name="missing-pokemon", description="Commands related to missing pokemon"
    )

    # 🎀────────────────────────────────────────────
    #          🌸 /missing-pokemon add 🌸
    # 🎀────────────────────────────────────────────
    @missing_pokemon_group.command(
        name="add", description="Adds missing Pokémon from your ;list pokemon command"
    )
    @app_commands.describe(
        message_link="Link to the PokéMeow message (must have embed with Pokémon list)",
        channel="Channel to send alerts",
        role="Optional role to ping",
        skip="What variant to skip (if any)",
    )
    async def missing_pokemon_add(
        self,
        interaction: discord.Interaction,
        message_link: str,
        channel: discord.TextChannel,
        role: discord.Role | None = None,
        skip: Literal[
            "Regular",
            "Shiny",
            "Golden",
            "Regular and Shiny",
            "Regular and Golden",
            "Shiny and Golden",
        ] = None,
    ):
        slash_cmd_name = "missing-pokemon add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_add_func,
            message_link=message_link,
            channel=channel,
            role=role,
            skip=skip,
        )
    # 🎀────────────────────────────────────────────
    #          🌸 /missing-pokemon list 🌸
    # 🎀────────────────────────────────────────────
    @missing_pokemon_group.command(
        name="list", description="List all of your missing Pokémon entries"
    )
    async def missing_pokemon_list(self, interaction: discord.Interaction):
        slash_cmd_name = "missing-pokemon list"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_list_func,
        )
    # 🎀────────────────────────────────────────────
    #          🌸 /missing-pokemon remove 🌸
    # 🎀────────────────────────────────────────────
    @missing_pokemon_group.command(
        name="remove", description="Removes a missing Pokémon entry by Dex number or all"
    )
    @app_commands.autocomplete(
        pokemon=user_missing_pokemon_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        pokemon="Pokemon name, Dex number, or 'all' to remove all alerts"
    )
    async def missing_pokemon_remove(self, interaction: discord.Interaction, pokemon: str):

        slash_cmd_name = "missing-pokemon remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_remove_func,
            pokemon=pokemon,
        )


# 🎀────────────────────────────────────────────
#           🌸 Cog Setup Function 🌸
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MissingPokemon(bot)
    await bot.add_cog(cog)
