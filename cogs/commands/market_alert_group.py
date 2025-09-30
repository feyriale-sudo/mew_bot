# 🎀────────────────────────────────────────────
#           🌸 Market Alerts Command Group 🌸
# ─────────────────────────────────────────────
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from utils.group_func.market_alert import *
from utils.pokemeow.autocomplete import pokemon_autocomplete, user_alerts_autocomplete


# 🎀────────────────────────────────────────────
#           🌸 MarketAlerts Cog Setup 🌸
# ─────────────────────────────────────────────
class MarketAlerts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎀────────────────────────────────────────────
    #           🌸 Slash Command Group 🌸
    # 🎀────────────────────────────────────────────
    market_alerts_group = app_commands.Group(
        name="market-alert", description="Commands related to market alerts"
    )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert add 🌸
    # 🎀────────────────────────────────────────────
    @market_alerts_group.command(name="add", description="Set a new market alert")
    @app_commands.autocomplete(pokemon=pokemon_autocomplete)  # 👈 attach autocomplete
    @app_commands.describe(
        pokemon="Pokemon name or Dex number",
        max_price="Maximum price in PokeCoin",
        channel="Channel to send alerts",
        role="(Desktop) Optional role to ping",
        mobile_role_input="(Mobile) Optional role to ping (<@role> | <@&role> | roleid)",
    )
    async def add_alert(
        self,
        interaction: discord.Interaction,
        pokemon: str,
        max_price: int,
        channel: discord.TextChannel,
        role: Optional[discord.Role] = None,  # 👈 must stay a Role for slash commands
        mobile_role_input: str = None,
    ):

        slash_cmd_name = "market-alert add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=add_market_alert_func,
            pokemon=pokemon,
            max_price=max_price,
            channel=channel,
            role=role,
            mobile_role_input=mobile_role_input,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert remove 🌸
    # 🎀────────────────────────────────────────────
    @market_alerts_group.command(
        name="remove",
        description="Remove a market alert for a Pokemon, Dex number, or all",
    )
    @app_commands.autocomplete(
        pokemon=user_alerts_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(
        pokemon="Pokemon name, Dex number, or 'all' to remove all alerts"
    )
    async def remove_alert(self, interaction: discord.Interaction, pokemon: str):

        slash_cmd_name = "market-alert remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=remove_market_alert_func,
            pokemon=pokemon,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert mine 🌸
    # 🎀────────────────────────────────────────────
    @market_alerts_group.command(
        name="mine", description="View all your active market alerts"
    )
    async def mine_alerts(self, interaction: discord.Interaction):

        slash_cmd_name = "market-alert mine"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=mine_market_alerts_func,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert toggle 🌸
    # 🎀────────────────────────────────────────────
    @market_alerts_group.command(
        name="toggle",
        description="Toggle whether a market alert notifies you (on/off)",
    )
    @app_commands.describe(
        pokemon="Pokemon name, Dex number, or 'all' to toggle all alerts",
        value="true = enable notifications, false = disable notifications",
    )
    async def toggle_alert(
        self, interaction: discord.Interaction, pokemon: str, value: bool
    ):

        slash_cmd_name = "market-alert toggle"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=toggle_market_alert_func,
            pokemon=pokemon,
            value=value,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert update 🌸
    # 🎀────────────────────────────────────────────
    @market_alerts_group.command(
        name="update",
        description="Updates a market alert for a Pokemon",
    )
    @app_commands.autocomplete(pokemon=user_alerts_autocomplete)
    @app_commands.describe(
        pokemon="Pokemon name or Dex number",
        max_price="Maximum price in PokeCoin",
        channel="Channel to send alerts",
        role="(Desktop) Optional role to ping",
        mobile_role_input="(Mobile) Optional role to ping (<@role> | <@&role> | roleid)",
        notify="Enable or disable notifications",
    )
    @app_commands.choices(
        notify=[
            app_commands.Choice(name="Enable", value="true"),
            app_commands.Choice(name="Disable", value="false"),
        ]
    )
    async def update_market_alert(
        self,
        interaction: discord.Interaction,
        pokemon: str,
        max_price: int | None = None,
        channel: discord.TextChannel | None = None,
        role: discord.Role | None = None,
        mobile_role_input: str = None,
        notify: str | None = None,  # Choice strings
    ):
        slash_cmd_name = "market-alert update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=update_market_alert_func,
            pokemon=pokemon,
            max_price=max_price,
            channel=channel,
            role=role,
            notify=notify,
            mobile_role_input=mobile_role_input,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /market-alert bulk-update 🌸
    # 🎀────────────────────────────────────────────

    @market_alerts_group.command(
        name="bulk-update",
        description="Change the channel or role for all of your existing market alerts at once",
    )
    @app_commands.describe(
        channel="Channel to send alerts",
        role="Role to ping (<@role> | <@&role> | roleid| type 'none' to remove the role)",
    )
    async def update_market_alert_bulk(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
        role: str = None,  # ✅ correct
    ):
        slash_cmd_name = "market-alert update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=update_market_alert_role_channel_func,
            channel=channel,
            role=role,
        )


# 🎀────────────────────────────────────────────
#           🌸 Cog Setup Function 🌸
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MarketAlerts(bot)
    await bot.add_cog(cog)
    market_alerts_group = (
        MarketAlerts.market_alerts_group
    )  # top-level app_commands.Group
    # await log_command_group_full_paths_to_cache(bot=bot, group=market_alerts_group)
