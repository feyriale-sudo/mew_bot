# ❀───────────────────────────────❀
#       💖  Imports  💖
# ❀───────────────────────────────❀
import asyncio
import glob
import logging
import os

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.db.get_pg_pool import *
from utils.logs.pretty_log import pretty_log, set_mew_bot
from utils.cache.centralized_cache import load_all_caches


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


# ❀───────────────────────────────❀
#      💖  Startup Tasks 💖
# ❀───────────────────────────────❀
@tasks.loop(count=1)
async def startup_tasks():
    await bot.wait_until_ready()
    # ❀ Load caches ❀
    await load_all_caches(bot)
    # ❀ Start cache refresher if not running ❀
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()

    await startup_checklist(bot)

# ❀───────────────────────────────❀
#      💖  Startup Checklist 💖
# ❀───────────────────────────────❀
async def startup_checklist(bot: commands.Bot):
    from utils.cache.cache_list import market_alert_cache

    # ❀ This divider stays untouched ❀
    print("\n୨୧ ⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔♡⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔⏔ ୨୧")
    print(f"✅ {len(bot.cogs)} 🌷 Cogs Loaded")
    print(f"✅ {len(market_alert_cache)} 🦄 Market Alerts")
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


if __name__ == "__main__":
    asyncio.run(main())
