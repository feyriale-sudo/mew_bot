import re
from datetime import datetime, timedelta

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.reminders.reminders_db_func import (
    fetch_user_reminder,
    update_user_reminder,
)
from utils.logs.pretty_log import pretty_log
from utils.parsers.reminder_parser import parse_remind_on, parse_repeat_interval
from utils.visuals.color_helpers import hex_to_dec
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# 🌸───────────────────────────────────────────────🌸
# 🩷⏰  REMINDER EDIT FUNCTION (USER REMINDER ID)  🩷
# 🌸───────────────────────────────────────────────🌸
async def edit_reminder_func(
    bot,
    interaction: discord.Interaction,
    reminder_id: int,
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
    """Edit a user's reminder with confirmation and bot log embed."""

    user = interaction.user
    user_id = user.id
    user_name = user.name

    loader = await pretty_defer(
        interaction=interaction, content=f"Editing your reminder...", ephemeral=False
    )

    # Fetch existing reminder
    reminder = await fetch_user_reminder(bot, user_id, reminder_id)
    if not reminder:
        await loader.error(content="Invalid reminder ID.")
        return

    log_channel = interaction.guild.get_channel(Channels.bot_logs)
    if not log_channel:
        await loader.error(content="Bot log channel not found.")
        return

    ping_role_1_id = ping_role_1.id if ping_role_1 else None
    ping_role_2_id = ping_role_2.id if ping_role_2 else None

    # Parse color
    dec_color = None
    if color:
        success, dec_color, error_msg = hex_to_dec(color)
        if not success:
            await loader.error(content=f"🎨 Invalid color: {error_msg}")
            return

    # Parse remind_on
    success, remind_on_ts, error_msg = parse_remind_on(remind_on)
    if not success:
        await loader.error(content=f"❌ {error_msg}")
        return

    # Parse repeat interval
    repeat_seconds = None
    if repeat_interval:
        success, repeat_seconds_or_error = parse_repeat_interval(repeat_interval)
        if not success:
            await loader.error(
                content=f"❌ Invalid repeat interval: {repeat_seconds_or_error}"
            )
            return
        repeat_seconds = repeat_seconds_or_error

    # Build dict of updated fields
    update_fields = {
        "message": message,
        "remind_on": remind_on_ts,
        "title": title,
        "ping_role_1": ping_role_1_id,
        "ping_role_2": ping_role_2_id,
        "repeat_interval": repeat_seconds,
        "color": dec_color,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "footer_text": footer_text,
    }
    # Remove fields that are None to avoid overwriting existing values
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    try:
        await update_user_reminder(bot, user_id, reminder_id, update_fields)
    except Exception as e:
        await loader.error(content="❌ Failed to update reminder.")
        pretty_log(
            tag="error",
            message=f"Failed to update reminder {reminder_id} for {user_name} ({user_id}): {e}",
            include_trace=True,
        )
        return

    # 🩷✅ Build confirmation embed
    embed = discord.Embed(
        title=f"Reminder Updated: ID {reminder_id}",
        description=(
            f"**Title:** {title or reminder['title']}\n"
            f"**Message:** {message or reminder['message']}\n"
            f"**Remind On:** <t:{int(remind_on_ts)}:F>"
        ),
        color=dec_color or reminder.get("color") or 0xFF66A3,
        timestamp=datetime.now(),
    )

    # Add optional fields if present
    if ping_role_1:
        embed.add_field(name="🩷 Ping Role 1", value=ping_role_1.mention, inline=True)
    if ping_role_2:
        embed.add_field(name="🩷 Ping Role 2", value=ping_role_2.mention, inline=True)
    if repeat_seconds:
        embed.add_field(
            name="🩷 Repeat Interval",
            value=f"{repeat_interval} ({repeat_seconds} seconds)",
            inline=True,
        )
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if footer_text:
        embed.set_footer(text=footer_text)

    embed = design_embed(user=user, embed=embed)

    # Send confirmation
    await loader.success(embed=embed, content="✅ Reminder updated!")

    pretty_log(
        tag="success",
        message=f"Reminder {reminder_id} updated for {user_name} ({user_id})",
    )

    # Log to bot channel
    if log_channel:
        try:
            log_embed = discord.Embed(
                title=f"🩷 Reminder Updated (ID {reminder_id})",
                description=(
                    f"- **Member:** {user.mention}\n"
                    f"- **Title:** {title or reminder['title']}\n"
                    f"- **Message:** {message or reminder['message']}\n"
                    f"- **Remind On:** <t:{int(remind_on_ts)}:F>\n"
                    f"{f'- **Repeat Interval:** {repeat_interval} ({repeat_seconds} seconds)\n' if repeat_seconds else ''}"
                    f"{f'- **Ping Role 1:** <@&{ping_role_1_id}>\n' if ping_role_1_id else ''}"
                    f"{f'- **Ping Role 2:** <@&{ping_role_2_id}>\n' if ping_role_2_id else ''}"
                    f"{f'- **Color:** {color}\n' if color else ''}"
                ),
                color=dec_color or reminder.get("color") or 0xFF66A3,
                timestamp=datetime.now(),
            )
            log_embed = design_embed(user=user, embed=log_embed)
            await log_channel.send(embed=log_embed)
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to log reminder update for {user_name} ({user_id}): {e}",
                include_trace=True,
            )
