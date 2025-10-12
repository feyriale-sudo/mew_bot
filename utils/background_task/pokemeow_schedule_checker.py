import re
from datetime import datetime

import discord

from config.aesthetic import *
from utils.db.schedule_db_func import (
    delete_reminder,
    fetch_all_schedules,
    fetch_due_reminders,
    fetch_user_schedule,
)
from utils.logs.pretty_log import pretty_log

SCHEDULE_MAP = {
    "catchbot": {
        "emoji": Emojis.catchbot,
    },
    "quest": {
        "emoji": Emojis.quest,
    },
}


# 🟣────────────────────────────────────────────
#       🐱 Pokemeow Schedule Checker 🐱
# 🟣────────────────────────────────────────────
async def pokemeow_schedule_checker(bot: discord.Client):
    """
    Background task to check Pokemeow schedules every minute.
    Sends reminders to users when their scheduled time arrives.
    """

    due_schedules = await fetch_due_reminders(bot)
    if not due_schedules:
        return

    for schedule in due_schedules:
        user_id = schedule["user_id"]
        user_name = schedule["user_name"]
        type_ = schedule["type"]
        channel_id = schedule.get("channel_id")
        reminder_id = schedule["reminder_id"]

        # Fetch the user
        user = bot.get_user(user_id)
        if not user:
            await delete_reminder(bot, reminder_id)
            pretty_log(
                tag="error",
                message=f"User ID {user_id} not found. Deleted reminder ID {reminder_id}.",
                bot=bot,
            )
            continue

        if channel_id:
            channel = bot.get_channel(channel_id)
            if not channel:
                await delete_reminder(bot, reminder_id)
                pretty_log(
                    tag="error",
                    message=f"Channel ID {channel_id} not found. Deleted reminder ID {reminder_id}.",
                    bot=bot,
                )
                continue
            display_emoji = SCHEDULE_MAP.get(type_, {}).get("emoji", "")
            content = ""
            if type_ == "catchbot":
                content = f"{display_emoji} {user.mention}, Your Catchbot has returned!"
            elif type_ == "quest":
                content = f"{display_emoji} {user.mention}, Your next quest is ready!"

            await channel.send(content=content)
            # delete reminder
            await delete_reminder(bot, reminder_id)
            pretty_log(
                tag="info",
                message=f"Sent {type_} reminder to {user_name} (ID: {user_id}) in channel ID {channel_id}. Deleted reminder ID {reminder_id}.",
                bot=bot,
            )
        else:
            try:
                display_emoji = SCHEDULE_MAP.get(type_, {}).get("emoji", "")
                content = ""
                if type_ == "catchbot":
                    content = f"{display_emoji} {user.mention}, Your Catchbot has returned!"
                elif type_ == "quest":
                    content = f"{display_emoji} {user.mention}, Your next quest is ready!"

                await user.send(content=content)
                # delete reminder
                await delete_reminder(bot, reminder_id)
                pretty_log(
                    tag="info",
                    message=f"Sent {type_} reminder to {user_name} (ID: {user_id}) via DM. Deleted reminder ID {reminder_id}.",
                    bot=bot,
                )
            except discord.Forbidden:
                # Cannot send DM to user
                await delete_reminder(bot, reminder_id)
                pretty_log(
                    tag="error",
                    message=f"Cannot send DM to user ID {user_id}. Deleted reminder ID {reminder_id}.",
                    bot=bot,
                )
