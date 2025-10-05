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
from utils.group_func.reminders.timezone_db_func import fetch_user_timezone

# 🌸───────────────────────────────────────────────🌸
# 🩷⏰  REMINDER EDIT FUNCTION (USER REMINDER ID)  🩷
# 🌸───────────────────────────────────────────────🌸
async def edit_reminder_func(
    bot,
    interaction: discord.Interaction,
    reminder_id: str,
    new_message: str = None,
    new_remind_on: str = None,
    new_title: str = None,
    new_ping_role_1: discord.Role = None,
    new_ping_role_2: discord.Role = None,
    new_repeat_interval: str = None,
    new_color: str = None,
    new_image_url: str = None,
    new_thumbnail_url: str = None,
    new_footer_text: str = None,
):
    """Edit a user's reminder with confirmation and bot log embed."""

    user = interaction.user
    user_id = user.id
    user_name = user.name
    reminder_id = int(reminder_id)

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

    new_ping_role_1_id = new_ping_role_1.id if new_ping_role_1 else None
    new_ping_role_2_id = new_ping_role_2.id if new_ping_role_2 else None

    # Initialize optional vars
    new_dec_color = None
    new_remind_on_ts = None
    new_repeat_seconds = None

    # Parse color
    new_dec_color = None
    if new_color:
        success, new_dec_color, error_msg = hex_to_dec(new_color)
        if not success:
            await loader.error(content=f"🎨 Invalid color: {error_msg}")
            return

    # Parse remind_on
    if new_remind_on:
        # ⏱ Parse remind_on
        tz_str = await fetch_user_timezone(bot=bot, user_id=user_id)
        if not tz_str:
            await loader.error(
                content="You need to set your timezone first using `/reminder timezone`."
            )
        success, new_remind_on_ts, error_msg = parse_remind_on(new_remind_on, tz_str)
        if not success:
            await loader.error(content=f"{error_msg}")
            return

    # Parse repeat interval
    new_repeat_seconds = None
    if new_repeat_interval:
        success, repeat_seconds_or_error = parse_repeat_interval(new_repeat_interval)
        if not success:
            await loader.error(
                content=f"Invalid repeat interval: {repeat_seconds_or_error}"
            )
            return
        new_repeat_seconds = repeat_seconds_or_error

    # Build dict of updated fields
    update_fields = {
        "message": new_message,
        "remind_on": new_remind_on_ts,
        "title": new_title,
        "ping_role_1": new_ping_role_1_id,
        "ping_role_2": new_ping_role_2_id,
        "repeat_interval": new_repeat_seconds,
        "color": new_dec_color,
        "image_url": new_image_url,
        "thumbnail_url": new_thumbnail_url,
        "footer_text": new_footer_text,
    }
    # Remove fields that are None to avoid overwriting existing values
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    # 🛑 Check if user actually updated something
    if not update_fields:
        await loader.error(
            content="You must update at least one field besides the reminder ID."
        )
        return
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
    remind_on_value = new_remind_on_ts or reminder["remind_on"]
    old_thumbnail_url = reminder["thumbnail_url"]
    old_image_url = reminder["image_url"]
    old_footer_text = reminder["footer_text"]

    embed = discord.Embed(
        title=f"Reminder Updated: ID {reminder_id}",
        description=(
            f"**Title:** {new_title or reminder['title']}\n"
            f"**Message:** {new_message or reminder['message']}\n"
            f"**Remind On:** <t:{int(remind_on_value)}:F>"
        ),
        color=new_dec_color or reminder.get("color") or 0xFF66A3,
        timestamp=datetime.now(),
    )

    # Add optional fields if present
    if new_ping_role_1:
        embed.add_field(
            name="🩷 Ping Role 1", value=new_ping_role_1.mention, inline=True
        )
    if new_ping_role_2:
        embed.add_field(
            name="🩷 Ping Role 2", value=new_ping_role_2.mention, inline=True
        )
    if new_repeat_seconds:
        embed.add_field(
            name="🩷 Repeat Interval",
            value=f"{new_repeat_interval} ({new_repeat_seconds} seconds)",
            inline=True,
        )

    thumbnail_url = new_thumbnail_url or old_thumbnail_url
    image_url = new_image_url or old_image_url
    footer_text = new_footer_text or old_footer_text

    embed = await design_embed(
        user=user,
        embed=embed,
        thumbnail_url=thumbnail_url,
        image_url=image_url,
        footer_text=footer_text,
    )

    # Send confirmation
    await loader.success(embed=embed, content="Reminder updated!")

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
                    f"- **Title:** {new_title or reminder['title']}\n"
                    f"- **Message:** {new_message or reminder['message']}\n"
                    f"- **Remind On:** <t:{int(remind_on_value)}:F>\n"
                    f"{f'- **Repeat Interval:** {new_repeat_interval} ({new_repeat_seconds} seconds)\n' if new_repeat_seconds else ''}"
                    f"{f'- **Ping Role 1:** <@&{new_ping_role_1_id}>\n' if new_ping_role_1_id else ''}"
                    f"{f'- **Ping Role 2:** <@&{new_ping_role_2_id}>\n' if new_ping_role_2_id else ''}"
                    f"{f'- **Color:** {new_color}\n' if new_color else ''}"
                ),
                color=new_dec_color or reminder.get("color") or 0xFF66A3,
                timestamp=datetime.now(),
            )
            log_embed = await design_embed(
                user=user,
                embed=embed,
                thumbnail_url=thumbnail_url,
                image_url=image_url,
                footer_text=footer_text,
            )
            await log_channel.send(embed=log_embed)
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to log reminder update for {user_name} ({user_id}): {e}",
                include_trace=True,
            )
