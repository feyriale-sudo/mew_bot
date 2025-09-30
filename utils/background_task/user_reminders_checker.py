import re
from datetime import datetime, timedelta

import discord
from discord.ui import Button, View

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.reminders.reminders_db_func import (
    fetch_due_reminders,
    remove_user_reminder,
    update_user_reminder,
)
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error

REMINDER_CHANNEL_ID = Channels.reminders


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PROCESS DUE REMINDERS LOOP FUNCTION        🩷
# 🌸───────────────────────────────────────────────🌸
async def process_due_reminders(bot):
    """Check due reminders and send them to the reminder channel.
    Repeats reminders if repeat_interval is set, otherwise deletes them.
    """
    reminders = await fetch_due_reminders(bot)
    if not reminders:
        return  # nothing to process

    reminder_channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if not reminder_channel:
        pretty_log(
            tag="error", message=f"Reminder channel {REMINDER_CHANNEL_ID} not found"
        )
        return

    for r in reminders:
        try:
            # Build the embed for the reminder
            embed = discord.Embed(
                title=r["title"] or "Reminder",
                description=r["message"],
                color=r["color"] or 0xFF66A3,
                timestamp=datetime.now(),
            )
            if r.get("image_url"):
                embed.set_image(url=r["image_url"])
            if r.get("thumbnail_url"):
                embed.set_thumbnail(url=r["thumbnail_url"])
            if r.get("footer_text"):
                embed.set_footer(text=r["footer_text"])

            # Prepare ping roles if any
            ping_text = ""
            if r.get("ping_role_1"):
                ping_text += f"<@&{r['ping_role_1']}> "
            if r.get("ping_role_2"):
                ping_text += f"<@&{r['ping_role_2']}> "

            # Send the reminder
            await reminder_channel.send(content=ping_text or None, embed=embed)

            # Handle repeat vs one-off
            if r.get("repeat_interval"):
                new_remind_on = r["remind_on"] + timedelta(seconds=r["repeat_interval"])
                await update_user_reminder(
                    bot,
                    r["user_id"],
                    r["user_reminder_id"],
                    {"remind_on": new_remind_on},
                )
                pretty_log(
                    tag="success",
                    message=f"🔁 Repeated reminder {r['user_reminder_id']} for user {r['user_id']}, next at {new_remind_on}",
                )
            else:
                await remove_user_reminder(bot, r["user_id"], r["user_reminder_id"])
                pretty_log(
                    tag="success",
                    message=f"🗑️ One-off reminder {r['user_reminder_id']} sent and deleted for user {r['user_id']}",
                )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to send/process reminder {r['user_reminder_id']} for user {r['user_id']}: {e}",
                include_trace=True,
            )
