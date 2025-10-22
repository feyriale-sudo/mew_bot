import discord

from config.aesthetic import Emojis
from utils.db.special_battle_timer_db import (
    fetch_due_special_battle_timers,
    remove_special_battle_timer,
)
from utils.db.spooky_hour_db import fetch_spooky_hour
from utils.logs.pretty_log import pretty_log


# 🍭 Background task to check for due special battle timers
async def special_battle_timer_checker(bot: discord.Client):
    """Background task that checks for due special battle timers every minute"""


    # Check if spooky hour is active
    spooky_hour = await fetch_spooky_hour(bot)
    if not spooky_hour:
        return  # No spooky hour active, skip checking battle timers


    # Fetch due special battle timers
    due_timers = await fetch_due_special_battle_timers(bot)
    if not due_timers:
        return  # No due timers

    for timer in due_timers:
        user_id = timer["user_id"]
        npc_name = timer["npc_name"]
        channel_id = timer["channel_id"]

        # Notify the user in the specified channel
        channel = bot.get_channel(channel_id)
        if channel:
            member = channel.guild.get_member(user_id)
            if member:
                # Remove timer from database
                content = f"{Emojis.battle_timer} {member.mention}, you can now battle {npc_name.title()} again!"
                desc = f";b npc {npc_name}"
                embed = discord.Embed(description=desc, color=0x00FF00)
                try:
                    await channel.send(content=content)
                    pretty_log(
                        "info",
                        f"Notified user {user_id} about special battle timer for npc {npc_name} and removed from database",
                    )
                    await remove_special_battle_timer(bot, user_id, npc_name)
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to notify user {user_id} for npc {npc_name}: {e}",
                    )
            else:
                pretty_log(
                    "warn",
                    f"Member {user_id} not found in guild {channel.guild.id} for notifying about special battle timer for npc {npc_name}",
                )

        else:
            pretty_log(
                "warn",
                f"Channel {channel_id} not found for notifying user {user_id} about special battle timer for npc {npc_name}",
            )
