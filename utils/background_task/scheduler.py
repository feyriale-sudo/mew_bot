from utils.essentials.schedule_manager import SchedulerManager
from utils.background_task.daily_fa_ball_reset import daily_faction_ball_reset
from utils.logs.pretty_log import pretty_log
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")

# 🌙───────────────────────────────────────────────🌙
#           Background Task Scheduler Setup
# 🌙───────────────────────────────────────────────🌙
async def setup_scheduler(bot):
    """Setup and start the scheduler with background tasks."""

    # Daily Faction Ball Reset at 12 pm Manila
    scheduler_manager.add_cron_job(
        daily_faction_ball_reset,
        name="daily_faction_ball_reset",
        hour=12,
        minute=0,
        args=[bot],
    )
    pretty_log(
        tag="background_task",
        message="Scheduled daily faction ball reset at 12:00 PM Manila time.",
        bot=bot,
    )

    # Start the scheduler
    scheduler_manager.start()

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager