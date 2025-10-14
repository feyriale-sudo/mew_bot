import discord
from utils.logs.pretty_log import pretty_log
from utils.db.daily_faction_ball_db import clear_daily_faction_ball

# 🍭──────────────────────────────────────────────
#   Daily Faction Ball Reset Task
# 🍭──────────────────────────────────────────────
async def daily_faction_ball_reset(bot):
    """Reset daily faction balls at midnight UTC."""
    try:
        await clear_daily_faction_ball(bot)
        pretty_log(
            tag="background_task",
            message="Daily faction balls have been reset.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error in daily faction ball reset task: {e}",
            bot=bot,
        )