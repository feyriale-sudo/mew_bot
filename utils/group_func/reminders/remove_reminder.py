import re
from datetime import datetime, timedelta

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.reminders.reminders_db_func import (
    fetch_all_user_reminders,
    fetch_user_reminder,
    remove_all_user_reminders,
    remove_user_reminder,
)
from utils.logs.pretty_log import pretty_log
from utils.parsers.reminder_parser import parse_remind_on, parse_repeat_interval
from utils.visuals.color_helpers import hex_to_dec
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ REMOVE REMINDER FUNCTION WITH FULL EMBEDS   🩷
# 🌸───────────────────────────────────────────────🌸
async def remove_reminder_func(bot, interaction: discord.Interaction, reminder_id: str):
    """Remove reminder workflow with detailed embeds and bot log."""

    user = interaction.user
    user_id = user.id
    user_name = user.name

    all_reminders = False
    display_reminder_id = f"Reminder ID: {reminder_id}"

    reminder_id_str = str(reminder_id)
    if reminder_id_str.lower() == "all":
        display_reminder_id = "All Reminders"
        all_reminders = True

    loader = await pretty_defer(
        interaction,
        f"Removing {display_reminder_id}...",
        ephemeral=True,
    )

    log_channel = interaction.guild.get_channel(Channels.bot_logs)

    if not all_reminders:
        # Fetch the single reminder
        reminder_id_int = int(reminder_id)  # safely convert string to int here
        reminder = await fetch_user_reminder(bot, user_id, reminder_id_int)
        if not reminder:
            await loader.error(content="Invalid reminder ID.")
            return

        # Remove the reminder
        await remove_user_reminder(bot, user_id, reminder_id_int)

        # Build embed showing deleted reminder
        embed = discord.Embed(
            title=f"🗑️ Removed Reminder {reminder_id_int}",
            description=(
                f"**Title:** {reminder['title'] or 'N/A'}\n"
                f"**Message:** {reminder['message']}\n"
                f"**Remind on:** <t:{int(reminder['remind_on'].timestamp())}:F>\n"
                f"{f'**Repeat Interval:** {reminder['repeat_interval']}s\n' if reminder['repeat_interval'] else ''}"
                f"{f'**Ping Role 1:** <@&{reminder['ping_role_1']}>\n' if reminder['ping_role_1'] else ''}"
                f"{f'**Ping Role 2:** <@&{reminder['ping_role_2']}>\n' if reminder['ping_role_2'] else ''}"
            ),
            color=reminder["color"] or 0xFF5555,
            timestamp=datetime.now(),
        )
        if reminder.get("image_url"):
            embed.set_image(url=reminder["image_url"])
        if reminder.get("thumbnail_url"):
            embed.set_thumbnail(url=reminder["thumbnail_url"])
        embed = design_embed(user=user, embed=embed)

        await loader.success(embed=embed)

        pretty_log(
            tag="success",
            message=f"🗑️ Removed reminder {reminder_id_int} for {user_name} ({user_id})",
        )

        # Log to bot channel
        if log_channel:
            await log_channel.send(embed=embed)

    else:
        # Fetch all reminders
        reminders = await fetch_all_user_reminders(bot, user_id)
        if not reminders:
            await loader.error(content="You have no reminders to remove.")
            return

        # Remove all
        await remove_all_user_reminders(bot, user_id)

        # Build embed summarizing deleted reminders
        desc = ""
        for r in reminders[:10]:  # limit to 10 for embed size
            desc += f"**{r['reminder_id']}: {r['title'] or r['message'][:20]}** — <t:{int(r['remind_on'].timestamp())}:F>\n"
        if len(reminders) > 10:
            desc += f"...and {len(reminders)-10} more reminders.\n"

        embed = discord.Embed(
            title=f"🗑️ Removed All Reminders ({len(reminders)})",
            description=desc,
            color=0xFF5555,
            timestamp=datetime.now(),
        )
        embed = design_embed(user=user, embed=embed)
        await loader.success(embed=embed)

        pretty_log(
            tag="success",
            message=f"🗑️ Removed all {len(reminders)} reminders for {user_name} ({user_id})",
        )

        # Log to bot channel
        if log_channel:
            await log_channel.send(embed=embed)
