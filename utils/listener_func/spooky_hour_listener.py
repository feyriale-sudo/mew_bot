import re

import discord

from utils.db.spooky_hour_db import (
    fetch_spooky_hour,
    remove_spooky_hour,
    upsert_spooky_hour,
)
from utils.logs.pretty_log import pretty_log
from config.settings import MAIN_SERVER_ID
BUMP_CHANNEL_ID = 1370878801277358080
SPOOKY_HOUR_ROLE_ID = 1330644911946465362


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Extract Spooky Hour Helper Functions
# 🤍💫────────────────────────────────────────────💫🤍
def extract_spooky_hour_ts(text: str):
    """
    Extracts the timestamp from the line containing '**Spooky Hour**' in the embed description.
    Returns the integer timestamp if found, else None.
    """
    for line in text.splitlines():
        if "**Spooky Hour**" in line:
            match = re.search(r"<t:(\d+):f>", line)
            if match:
                return int(match.group(1))
    return None


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour Listener Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def handle_spooky_hour_hw_embed(bot: discord.Client, message: discord.Message):
    """
    Handles the Spooky Hour embed in the given message.
    Extracts the timestamp and upserts/removes from DB accordingly.
    """
    if not message.embeds:
        return

    embed = message.embeds[0]
    if not embed.description:
        return
    main_guild = bot.get_guild(MAIN_SERVER_ID)
    event_tracker_channel = main_guild.get_channel(BUMP_CHANNEL_ID)
    spooky_hour_role = main_guild.get_role(SPOOKY_HOUR_ROLE_ID)
    if "[INACTIVE]" not in embed.description:
        ends_on = extract_spooky_hour_ts(embed.description)
        if ends_on:
            # Check for existing schedule first
            existing_spooky_hour_info = await fetch_spooky_hour(bot)
            if existing_spooky_hour_info:
                existing_ends_on = existing_spooky_hour_info["ends_on"]
                existing_message_id = existing_spooky_hour_info["message_id"]

                if existing_ends_on != ends_on:
                    await upsert_spooky_hour(bot, ends_on, existing_message_id)
                elif existing_ends_on == ends_on:
                    pretty_log(
                        "info",
                        f"Same schedule already exists with ends_on {ends_on}",
                    )
                    return
            else:
                # No existing schedule, insert new
                content = f"{spooky_hour_role.mention} Spooky hour is here!"
                new_message = await event_tracker_channel.send(content=content)
                await upsert_spooky_hour(bot, ends_on, new_message.id)
                pretty_log(
                    "success",
                    f"Inserted new spooky_hour with ends_on {ends_on} and message_id {new_message.id}",
                )
                return

    elif "[INACTIVE]" in embed.description:
        # Check if there is existing schedule to remove
        existing_ends_on = await fetch_spooky_hour(bot)
        if existing_ends_on:
            await remove_spooky_hour(bot)
            content = f"{spooky_hour_role.mention} Spooky hour has ended."
            await event_tracker_channel.send(content=content)
            pretty_log(
                "success",
                "Removed existing spooky_hour schedule",
            )
        else:
            pretty_log(
                "info",
                "No existing spooky_hour schedule to remove",
            )
            return
