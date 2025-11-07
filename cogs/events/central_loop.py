import asyncio

from discord.ext import commands

# 🧹 Import your scheduled tasks
from utils.background_task.user_reminders_checker import process_due_reminders
from utils.background_task.pokemeow_schedule_checker import pokemeow_schedule_checker
from utils.logs.pretty_log import pretty_log
from utils.background_task.special_battle_timer_checker import special_battle_timer_checker
from utils.background_task.spooky_hour_checker import check_and_handle_spooky_hour_expiry

# 🍰──────────────────────────────
#   🎀 Cog: CentralLoop
#   Handles background tasks every 60 seconds
# 🍰──────────────────────────────
class CentralLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop_task = None

    def cog_unload(self):
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()
            pretty_log(
                "warn",
                "Loop task cancelled on cog unload.",
                label="CENTRAL LOOP",
                bot=self.bot,
            )

    async def central_loop(self):
        """Background loop that ticks every 60 seconds"""
        await self.bot.wait_until_ready()
        pretty_log(
            "",
            "✅ Central loop started!",
            label="🍭 CENTRAL LOOP",
            bot=self.bot,
        )
        while not self.bot.is_closed():
            try:
                pretty_log(
                    "",
                    "🔂 Running background checks...",
                    label="🍭 CENTRAL LOOP",
                    bot=self.bot,
                )

                # 🦭 Check if any user reminder is due
                await process_due_reminders(self.bot)

                # 🐱 Check if any Pokemeow schedule reminder is due
                await pokemeow_schedule_checker(self.bot)

                # 🌹 Check for due special battle timers (Disabled for now)
                #await special_battle_timer_checker(self.bot)

                # 🍑 Check and handle Spooky Hour expiry (Disabled for now)
                #await check_and_handle_spooky_hour_expiry(self.bot)

            except Exception as e:
                pretty_log(
                    "error",
                    f"{e}",
                    label="CENTRAL LOOP ERROR",
                    bot=self.bot,
                )
            await asyncio.sleep(60)  # ⏱ tick interval

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the loop automatically once the bot is ready"""
        if not self.loop_task:
            self.loop_task = asyncio.create_task(self.central_loop())


# ====================
# 🔹 Setup
# ====================
async def setup(bot: commands.Bot):
    cog = CentralLoop(bot)
    await bot.add_cog(cog)

    print("\n[📋 CENTRAL LOOP CHECKLIST] Scheduled tasks loaded:")
    print("  ─────────────────────────────────────────────")
    print("  ✅ 🧭  process_due_reminders")
    print("  ✅ 🐱  pokemeow_schedule_checker")
    #print("  ✅ 🌹  special_battle_timer_checker")
    #print("  ✅ 🍑  check_and_handle_spooky_hour_expiry")
    print("  🍭 CentralLoop ticking every 60 seconds!")
    print("  ─────────────────────────────────────────────\n")
