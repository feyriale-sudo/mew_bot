import re
from datetime import datetime, timedelta

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.reminders.reminders_db_func import upsert_user_reminder
from utils.logs.pretty_log import pretty_log
from utils.parsers.reminder_parser import parse_remind_on, parse_repeat_interval
from utils.visuals.color_helpers import hex_to_dec
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error
from utils.group_func.reminders.timezone_db_func import fetch_user_timezone

# 🌸───────────────────────────────────────────────🌸
# 🩷⏰  REMINDER CREATION FUNCTION                 🩷
# 🌸───────────────────────────────────────────────🌸
async def add_reminder_func(
    bot,
    interaction: discord.Interaction,
    message: str,
    remind_on: str,
    title: str,
    ping_role_1: discord.Role = None,
    ping_role_2: discord.Role = None,
    repeat_interval: str = None,
    color: str = None,
    image_url: str = None,
    thumbnail_url: str = None,
    footer_text: str = None,
):
    """Add reminder workflow using pretty_defer:
    - Immediate loader with safe edits
    - Updates steps live
    """
    # 🩷👤 Prepare user & loader
    user = interaction.user
    user_id = user.id
    user_name = user.name

    ping_role_1_id = ping_role_1.id if ping_role_1 else None
    ping_role_2_id = ping_role_2.id if ping_role_2 else None

    loader = await pretty_defer(
        interaction=interaction, content="Setting your reminder...", ephemeral=True
    )

    log_channel = interaction.guild.get_channel(Channels.bot_logs)
    if not log_channel:
        await loader.error(content="Bot log channel not found.")
        return

    # 🩷🎨 Parse color (optional)
    dec_color = None
    if color:
        success, dec_color, error_msg = hex_to_dec(color)
        if not success:
            await loader.error(content=f"🎨 Invalid color: {error_msg}")
            return

    # ⏱ Parse remind_on
    tz_str = await fetch_user_timezone(bot=bot, user_id=user_id)
    if not tz_str:
        await loader.error(
            content="You need to set your timezone first using `/reminder timezone`."
        )

    # 🩷⏱ Parse remind_on
    success, remind_on_ts, error_msg = parse_remind_on(remind_on, tz_str)
    if not success:
        await loader.error(content=f"❌ {error_msg}")
        return

    # 🩷🔁 Parse repeat interval (optional)
    repeat_seconds = None
    if repeat_interval:
        success, repeat_seconds_or_error = parse_repeat_interval(repeat_interval)
        if not success:
            await loader.error(
                content=f"❌ Invalid repeat interval: {repeat_seconds_or_error}"
            )
            return
        repeat_seconds = repeat_seconds_or_error

    # 🩷💾 Insert reminder into DB
    try:
        await upsert_user_reminder(
            bot=bot,
            user_id=user_id,
            user_name=user_name,
            message=message,
            ping_role_1=ping_role_1_id,
            ping_role_2=ping_role_2_id,
            remind_on=remind_on_ts,
            repeat_interval=repeat_seconds,
            title=title,
            color=dec_color,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            footer_text=footer_text,
        )
    except Exception as e:
        await loader.error(content="Failed to set reminder.")
        pretty_log(
            tag="error",
            message=f"Failed to set reminder for {user_name} ({user_id}): {e}",
            include_trace=True,
        )
        return

    # 🩷✅ Build confirmation embed
    embed = discord.Embed(
        title=title or "Reminder set successfully",
        description=f"**Message:** {message}\n**Remind on:** <t:{remind_on_ts}:F>",
        color=dec_color or 0xFF66A3,
    )

    if ping_role_1:
        embed.add_field(
            name="🩷 Ping Role 1", value=f"{ping_role_1.mention}", inline=True
        )
    if ping_role_2:
        embed.add_field(
            name="🩷 Ping Role 2", value=f"{ping_role_2.mention}", inline=True
        )
    if repeat_seconds:
        embed.add_field(
            name="🩷 Repeat Interval",
            value=f"{repeat_interval} ({repeat_seconds} seconds)",
            inline=True,
        )

    embed = await design_embed(
        user=user,
        embed=embed,
        thumbnail_url=thumbnail_url,
        image_url=image_url,
        footer_text=footer_text,
    )

    # 🩷🎉 Send confirmation and log success
    await loader.success(embed=embed, content="Reminder set!")
    pretty_log(
        tag="success",
        message=f"Reminder set for {user_name} ({user_id}): '{message}' "
        f"Remind on <t:{remind_on_ts}:F> "
        f"{f'with repeat {repeat_interval}' if repeat_interval else ''} "
        f"{f'color {color}' if color else ''}",
    )

    # 🩷📝 Log to bot channel
    try:
        log_embed = discord.Embed(
            title="🩷 New Reminder Set",
            description=(
                f"- **Member:** {user.mention}\n"
                f"- **Message:** {message}\n"
                f"- **Remind on:** <t:{remind_on_ts}:F>\n"
                f"{f'- **Repeat Interval:** {repeat_interval} ({repeat_seconds} seconds)\n' if repeat_seconds else ''}"
                f"{f'- **Ping Role 1:** <@&{ping_role_1_id}>\n' if ping_role_1_id else ''}"
                f"{f'- **Ping Role 2:** <@&{ping_role_2_id}>\n' if ping_role_2_id else ''}"
                f"{f'- **Color:** {color}\n' if color else ''}"
            ),
            color=dec_color or 0xFF66A3,
            timestamp=datetime.now(),
        )
        log_embed = await design_embed(user=user, embed=log_embed)
        await log_channel.send(embed=log_embed)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to log reminder for {user_name} ({user_id}): {e}",
            include_trace=True,
        )
