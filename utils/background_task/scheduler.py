import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.background_task.bt_reset_reminder import (
    battle_tower_reset_reminder,
    clear_battle_tower_reminders,
)
from utils.background_task.daily_fa_ball_reset import daily_faction_ball_reset
from utils.background_task.daily_pokemeow_reminder import daily_pokemeow_reminder
from utils.essentials.schedule_manager import SchedulerManager
from utils.logs.pretty_log import pretty_log

scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")
NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT


# 🌙───────────────────────────────────────────────🌙
#           Background Task Scheduler Setup
# 🌙───────────────────────────────────────────────🌙
async def setup_scheduler(bot):
    """Setup and start the scheduler with background tasks."""

    # Daily Faction Ball Reset at 12 AM EST
    scheduler_manager.add_cron_job(
        daily_faction_ball_reset,
        name="daily_faction_ball_reset",
        hour=0,
        minute=0,
        args=[bot],
        timezone=NYC,
    )
    pretty_log(
        tag="background_task",
        message="Scheduled daily faction ball reset at 12:00 AM EST.",
        bot=bot,
    )

    # Daily Pokemeow Reminder at 12 AM EST
    scheduler_manager.add_cron_job(
        daily_pokemeow_reminder,
        name="daily_pokemeow_reminder",
        hour=0,
        minute=0,
        args=[bot],
        timezone=NYC,
    )
    pretty_log(
        tag="background_task",
        message="Scheduled daily Pokemeow reminder at 12:00 AM EST.",
        bot=bot,
    )

    # Battle Tower Reset Reminder at 8:05 PM EST Every Monday , Wednesday, Friday
    scheduler_manager.add_cron_job(
        battle_tower_reset_reminder,
        name="battle_tower_reset_reminder",
        day_of_week="mon,wed,fri",
        hour=20,
        minute=5,
        args=[bot],
        timezone=NYC,
    )
    pretty_log(
        tag="background_task",
        message="Scheduled Battle Tower reset reminders on Mon, Wed, Fri at 8:05 PM EST.",
        bot=bot,
    )

    # Clear Battle Tower Reset Reminder at 9:05 PM EST Every Monday , Wednesday, Friday
    scheduler_manager.add_cron_job(
        clear_battle_tower_reminders,
        name="clear_battle_tower_reminders",
        day_of_week="mon,wed,fri",
        hour=21,
        minute=5,
        args=[bot],
        timezone=NYC,
    )
    pretty_log(
        tag="background_task",
        message="Scheduled clearing of Battle Tower reminders on Mon, Wed, Fri at 9:05 PM EST.",
        bot=bot,
    )

    # Start the scheduler
    scheduler_manager.start()

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager
