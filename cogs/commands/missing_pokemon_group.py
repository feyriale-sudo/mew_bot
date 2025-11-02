# 🎀────────────────────────────────────────────
#    🌸 Missing Pokemon Command Group 🌸
# ─────────────────────────────────────────────
from typing import Literal, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.db.missing_pokemon_db_func import user_missing_pokemon_autocomplete
from utils.essentials.command_safe import run_command_safe
from utils.group_func.missing_pokemon import *
from utils.pokemeow.autocomplete import pokemon_autocomplete


# 🎀────────────────────────────────────────────
#           🌸 MissingPokemon Cog Setup 🌸
# ─────────────────────────────────────────────
class MissingPokemon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎀────────────────────────────────────────────
    #           🌸 Slash Command Group 🌸
    # 🎀────────────────────────────────────────────
    checklist_group = app_commands.Group(
        name="checklist", description="Commands related to missing pokemon"
    )

    # 🎀────────────────────────────────────────────
    #          🌸 /checklist add 🌸
    # 🎀────────────────────────────────────────────
    @checklist_group.command(
        name="add", description="Adds a missing Pokémon to your checklist"
    )
    @app_commands.autocomplete(pokemon=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.describe(
        pokemon="Name of the Pokémon",
    )
    async def missing_pokemon_add(
        self,
        interaction: discord.Interaction,
        pokemon: str,
    ):
        slash_cmd_name = "checklist add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_add_func,
            pokemon=pokemon,
        )

    # 🎀────────────────────────────────────────────
    #          🌸 /checklist box 🌸
    # 🎀────────────────────────────────────────────
    @checklist_group.command(
        name="box", description="Adds missing Pokémon from your ;list pokemon command"
    )
    @app_commands.describe(
        message_link="Link to the PokéMeow message (must have embed with Pokémon list)",
        skip="What variant to skip (if any)",
    )
    async def missing_pokemon_box(
        self,
        interaction: discord.Interaction,
        message_link: str,
        skip: Literal[
            "Regular",
            "Shiny",
            "Golden",
            "Regular and Shiny",
            "Regular and Golden",
            "Shiny and Golden",
        ] = None,
    ):
        slash_cmd_name = "checklist add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_box_func,
            message_link=message_link,
            skip=skip,
        )

    # 🎀────────────────────────────────────────────
    #          🌸 /checklist view 🌸
    # 🎀────────────────────────────────────────────
    @checklist_group.command(
        name="view", description="Lets you view all of your missing Pokémon entries"
    )
    async def missing_pokemon_list(self, interaction: discord.Interaction):
        slash_cmd_name = "checklist view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=missing_pokemon_list_func,
        )

    # 🎀────────────────────────────────────────────
    #          🌸 /checklist remove 🌸
    # 🎀────────────────────────────────────────────
    @checklist_group.command(
        name="remove",
        description="Removes a missing Pokémon entry by Dex number or all",
    )
    @app_commands.autocomplete(
        pokemon=user_missing_pokemon_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        pokemon="Pokemon name, Dex number, or 'all' to remove all alerts"
    )
    async def missing_pokemon_remove(
        self, interaction: discord.Interaction, pokemon: str
    ):

        slash_cmd_name = "checklist remove"

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
