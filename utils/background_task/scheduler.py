import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.background_task.daily_fa_ball_reset import daily_faction_ball_reset
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

    # Start the scheduler
    scheduler_manager.start()

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager
