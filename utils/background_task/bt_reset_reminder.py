import discord

from config.fairy_tale_constants import FAIRY_TAIL__TEXT_CHANNELS
from utils.db.battletower_db import (
    clear_battletower_registrations,
    fetch_battletower_users,
)
from utils.logs.pretty_log import pretty_log


# 🍡──────────────────────────────────────────────
#   Battle Tower Reset Reminder
# 🍡──────────────────────────────────────────────
async def battle_tower_reset_reminder(bot):
    """Send a reminder to Battle Tower users about the daily reset."""
    rows = await fetch_battletower_users(bot)
    if not rows:
        pretty_log(
            tag="background_task",
            message="No Battle Tower users found for reset reminder.",
            bot=bot,
        )
        return
    channel = bot.get_channel(FAIRY_TAIL__TEXT_CHANNELS.amnesia)
    user_mentions = []
    for row in rows:
        user_id = row["user_id"]
        user = bot.get_user(user_id)
        if user:
            user_mentions.append(user.mention)
    if user_mentions:
        mention_text = " ".join(user_mentions)
        reminder_message = f"{mention_text} One hour left until Battle Tower resets!\n"
        await channel.send(reminder_message)
        pretty_log(
            tag="background_task",
            message="Sent Battle Tower reset reminder to users.",
            bot=bot,
        )


async def clear_battle_tower_reminders(bot):
    """Clear all Battle Tower reminders (if any)."""
    try:
        await clear_battletower_registrations(bot)
        pretty_log(
            tag="background_task",
            message="Cleared all Battle Tower reminders.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error clearing Battle Tower reminders: {e}",
            bot=bot,
        )
