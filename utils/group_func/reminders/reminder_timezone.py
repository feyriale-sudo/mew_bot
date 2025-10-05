import discord
import pytz
from discord import app_commands
from discord.ext import commands

from config.settings import Channels
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error

from .timezone_db_func import set_user_timezone


# -------------------- [💙 SET TIMEZONE FUNC] --------------------


async def reminder_set_timezone_func(
    bot: commands.Bot, interaction: discord.Interaction, timezone: str
):
    """Set the user's timezone for reminders."""
    handler = await pretty_defer(
        interaction=interaction, content="Setting your timezone...", ephemeral=True
    )
    user = interaction.user
    user_id = user.id
    user_name = user.name

    # -------------------- [💙 SET TIMEZONE] --------------------
    await set_user_timezone(
        bot=bot, user_id=user_id, user_name=user_name, timezone=timezone
    )

    # -------------------- [💙 USER CONFIRM EMBED] --------------------
    user_embed = discord.Embed(
        title="Timezone set successfully", description=f"Timezone: {timezone}"
    )
    user_embed = await design_embed(
        user=user,
        embed=user_embed,
    )

    # -------------------- [💙 SERVER LOG EMBED] --------------------
    server_embed = discord.Embed(
        title="Timezone updated",
        description=f"- Member: {user.mention}\n- Timezone: {timezone}",
    )
    server_embed = await design_embed(
        user=user,
        embed=server_embed,
    )

    # -------------------- [💙 SEND EMBEDS] --------------------
    await handler.success(embed=user_embed, content="")

    # Server log
    log_channel = interaction.user.guild.get_channel(Channels.bot_logs)
    if log_channel:
        await log_channel.send(embed=server_embed)

    # -------------------- [💙 PRETTY LOG] --------------------
    pretty_log(
        "db",
        f"🌙 {user_name} ({user_id}) set timezone → {timezone}",
    )
