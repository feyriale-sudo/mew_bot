# ❀───────────────────────────────❀
#       💖  Imports  💖
# ❀───────────────────────────────❀
import asyncio

import glob
import logging
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.background_task.scheduler import setup_scheduler
from utils.cache.centralized_cache import load_all_caches
from utils.db.get_pg_pool import *
from utils.logs.pretty_log import pretty_log, set_mew_bot
from utils.cache.processed_msg_ids import clear_processed_msg_ids
# ❀───────────────────────────────❀
#       💖  Suppress Logs  💖
# ❀───────────────────────────────❀
logging.basicConfig(level=logging.CRITICAL)
for logger_name in [
    "discord",
    "discord.gateway",
    "discord.http",
    "discord.voice_client",
    "asyncio",
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)


# ❀───────────────────────────────❀
#       💖  Bot Factory  💖
# ❀───────────────────────────────❀
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
set_mew_bot(bot)


# ❀───────────────────────────────❀
#   💖  Prefix Command Error Handler 💖
# ❀───────────────────────────────❀
@bot.event
async def on_command_error(ctx, error):
    # Ignore prefix command not found
    if isinstance(error, commands.CommandNotFound):
        return

    # Handle other prefix errors
    await ctx.send("❌ Something went wrong.")
    pretty_log(
        tag="error",
        message=f"Prefix command error: {error}",
        include_trace=True,
    )


# ❀───────────────────────────────────────────────❀
#      💖 Timezone Configuration (Singapore) 💖
# ❀───────────────────────────────────────────────❀
ASIA_SINGAPORE = ZoneInfo("Asia/Singapore")


# 🌸───────────────────────────────────────────────🌸
# 💖 Mew Status Rotations (Skaia + Market themed) 💖
# 🌸───────────────────────────────────────────────🌸

MEW_MORNING_STATUSES = [
    (discord.ActivityType.playing, "with Skaia's hair ˚₊⊹♡"),
    (discord.ActivityType.playing, "with Skaia's morning coffee ₊˚☕︵♡"),
    (discord.ActivityType.playing, "with Skaia's Mew shopping list ⋆｡˚🛒♡"),
    (discord.ActivityType.playing, "with pink reminders for Skaia ୨୧₊˚♡"),
    (discord.ActivityType.listening, "to Skaia's soft alarm chimes ⋆｡˚🔔⊹♡"),
    (discord.ActivityType.watching, "over Skaia's busy timers ˚₊· ͟͟͞͞➳♡"),
    (discord.ActivityType.playing, "with reminders as bright as Skaia ˚ʚ♡ɞ˚"),
]

MEW_NIGHT_STATUSES = [
    (discord.ActivityType.playing, "with starlit reminders for Skaia ⋆˙⟡♡"),
    (discord.ActivityType.playing, "with pink dreams in the market ｡˚୨୧˚｡"),
    (discord.ActivityType.playing, "with quiet timers as Skaia rests ₊˚✧ ﾟ."),
    (discord.ActivityType.listening, "Skaia's sleepy reminders ₊˚.⋆𐙚₊˚⊹♡"),
    (discord.ActivityType.watching, "over Skaia's night market alerts ｡ﾟ•┈୨♡୧┈•ﾟ｡"),
    (discord.ActivityType.playing, "with starry timers and pink wishes ⊹₊ ⊹⋆˚｡𖦹"),
]

MEW_DEFAULT_STATUSES = [
    (discord.ActivityType.watching, "everyday alerts for Skaia ｡･:*:･ﾟ★,｡･:*:･ﾟ☆"),
    (discord.ActivityType.listening, "Skaia's reminder bells ♡₊˚︶꒷🎀꒷︶˚₊♡"),
    (discord.ActivityType.watching, "Skaia shop for Mews at the market 𓆩♡𓆪"),
    (discord.ActivityType.listening, "whispers of the market ₊˚⊹♡₊˚⊹"),
]


# ❀───────────────────────────────❀
#      💖  Pick Status 💖
# ❀───────────────────────────────❀
def pick_status_tuple():
    now = datetime.now(ASIA_SINGAPORE)
    pool = MEW_MORNING_STATUSES if 6 <= now.hour < 18 else MEW_NIGHT_STATUSES
    return random.choice(pool)


# ❀───────────────────────────────❀
#      💖  Refresh All Caches 💖
# ❀───────────────────────────────❀
@tasks.loop(hours=1)
async def refresh_all_caches():
    # ❀ Skip the very first run ❀
    if not hasattr(refresh_all_caches, "has_run"):
        refresh_all_caches.has_run = True
        return

    await load_all_caches(bot)

    # Clear processed messsage ids
    clear_processed_msg_ids()


# ❀───────────────────────────────❀
#      💖  Status Rotator 💖
# ❀───────────────────────────────❀
@tasks.loop(minutes=5)
async def status_rotator():
    activity_type, message = pick_status_tuple()
    pretty_log(
        "", "👒  STATUS ROTATOR", f"Switching status → {activity_type.name}: {message}"
    )
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


# ❀───────────────────────────────❀
#      💖  Startup Tasks 💖
# ❀───────────────────────────────❀
@tasks.loop(count=1)
async def startup_tasks():
    await bot.wait_until_ready()

    # ❀ Load caches ❀
    await load_all_caches(bot)

    # ❀ Sync market cache to DB once on startup ❀
    from utils.cache.cache_list import market_value_cache
    from utils.db.market_value_db_func import sync_market_cache_to_db

    if market_value_cache:
        await sync_market_cache_to_db(bot, market_value_cache)
        pretty_log(
            tag="sync", 
            message=f"Market cache synced ON STARTUP: {len(market_value_cache)} entries",
        )
    else:
        pretty_log(
            tag="sync",
            message="Market cache empty on startup, skipping sync",
        )

    # ❀ Start cache refresher if not running ❀
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()

    # ❀ Start status rotator if not running ❀
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="🩷 Playing with Skaia")
    )

    # ❀ Run startup checklist ❀
    await startup_checklist(bot)


# ❀───────────────────────────────❀
#      💖  Startup Checklist 💖
# ❀───────────────────────────────❀
async def startup_checklist(bot: commands.Bot):
    from utils.cache.cache_list import (
        daily_faction_ball_cache,
        market_alert_cache,
        market_value_cache,
        missing_pokemon_cache,
        schedule_cache,
        timer_cache,
        user_info_cache,
        utility_cache,
    )

    # ❀ This divider stays untouched ❀
    print("\n୨୧ ⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔♡⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔ ୨୧")
    print(f"✅ {len(bot.cogs)} 🌷 Cogs Loaded")
    print(f"✅ {len(market_alert_cache)} 🦄 Market Alerts")
    print(f"✅ {len(market_value_cache)} 💎 Market Values")
    print(f"✅ {len(missing_pokemon_cache)} 🐰 Missing Pokémon Alerts")
    print(f"✅ {len(timer_cache)} ⌚ Timer Settings Loaded")
    print(f"✅ {len(schedule_cache)} 📅 Schedule Settings Loaded")
    print(f"✅ {len(utility_cache)} 👚 Utility Settings Loaded")
    print(f"✅ {len(user_info_cache)} 🩰 User Info Loaded")
    print(f"✅ {len(daily_faction_ball_cache)} 🎈 Daily Faction Balls Loaded")
    print(f"✅ {startup_tasks.is_running()} 💄  Startup Tasks Running")
    pg_status = "Ready" if hasattr(bot, "pg_pool") else "Not Ready"
    print(f"✅ {pg_status} 🌺  PostgreSQL Pool")
    total_slash_commands = sum(1 for _ in bot.tree.walk_commands())
    print(f"✅ {total_slash_commands} 🧸 Slash Commands Synced")
    print("୨୧ ⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔♡⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔ ୨୧\n")


# ❀───────────────────────────────❀
#       💖  Event Hooks 💖
# ❀───────────────────────────────❀
# ❀ On Ready ❀
@bot.event
async def on_ready():
    pretty_log("ready", f"Mew bot awake as {bot.user}")

    # ❀ Sync slash commands ❀
    await bot.tree.sync()

    # ❀ Start startup tasks ❀
    if not startup_tasks.is_running():
        startup_tasks.start()


# ❀───────────────────────────────❀
#       💖  Setup Hook 💖
# ❀───────────────────────────────❀
@bot.event
async def setup_hook():
    # ❀ PostgreSQL connection ❀
    try:
        bot.pg_pool = await get_pg_pool()
    except Exception as e:
        pretty_log("critical", f"Postgres connection failed: {e}", include_trace=True)

    # ❀ Load all cogs ❀
    for cog_path in glob.glob("cogs/**/*.py", recursive=True):
        relative_path = os.path.relpath(cog_path, "cogs")
        module_name = relative_path[:-3].replace(os.sep, ".")
        cog_name = f"cogs.{module_name}"
        try:
            await bot.load_extension(cog_name)
        except Exception as e:
            pretty_log("error", f"Failed to load {cog_name}: {e}", include_trace=True)

    # ❀ Setup background task scheduler ❀
    await setup_scheduler(bot)
    bot.scheduler_manager = bot.scheduler_manager or None


# ❀───────────────────────────────❀
#       💖  Main Async Runner 💖
# ❀───────────────────────────────❀
async def main():
    load_dotenv()
    pretty_log("ready", "Mew Bot is starting...")

    retry_delay = 5
    while True:
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except KeyboardInterrupt:
            pretty_log("ready", "Shutting down Mew Bot...")
            break
        except Exception as e:
            pretty_log("error", f"Bot crashed: {e}", include_trace=True)
            pretty_log("ready", f"Restarting Mew Bot in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)


# ❀───────────────────────────────❀
#       💖  Entry Point 💖
# ❀───────────────────────────────❀
if __name__ == "__main__":
    asyncio.run(main())
