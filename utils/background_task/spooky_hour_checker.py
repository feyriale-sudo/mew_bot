from datetime import datetime

import discord

from utils.db.spooky_hour_db import fetch_spooky_hour, remove_spooky_hour
from utils.logs.pretty_log import pretty_log

BUMP_CHANNEL_ID = 1370878801277358080
SPOOKY_HOUR_ROLE_ID = 1330644911946465362


# 🕒────────────────────────────────────────────
#     ✨ Spooky Hour Checker
#     Checks if Spooky Hour has ended
# 🕒────────────────────────────────────────────
async def check_and_handle_spooky_hour_expiry(bot: discord.Client):
    """Checks if Spooky Hour has ended and removes the schedule if so."""
    now = int(datetime.now().timestamp())

    # Fetch current Spooky Hour schedule
    spooky_hour_info = await fetch_spooky_hour(bot)
    if not spooky_hour_info:
        return  # No Spooky Hour scheduled

    ends_on = spooky_hour_info["ends_on"]
    if now >= ends_on:
        try:
            # Remove Spooky Hour schedule from DB
            await remove_spooky_hour(bot)
            event_tracker_channel = bot.get_channel(BUMP_CHANNEL_ID)
            guild = event_tracker_channel.guild
            spooky_hour_role = guild.get_role(SPOOKY_HOUR_ROLE_ID)
            content = f"{spooky_hour_role.mention} Spooky hour has ended."
            await event_tracker_channel.send(content=content)

            # Log successful removal
            pretty_log(
                "info",
                f"Spooky Hour ended automatically at {now}, schedule removed.",
            )

        except Exception as e:
            # Log any errors during removal
            pretty_log(
                "error",
                f"Failed to remove Spooky Hour schedule: {type(e).__name__}: {e}",
            )
