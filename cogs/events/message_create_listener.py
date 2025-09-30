# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.settings import *
from utils.listener_func.market_alert_listener import process_market_alert_message
from utils.logs.pretty_log import pretty_log


class MessageCreateListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 💜 Helper: Retry Discord calls on 503
    async def retry_discord_call(self, func, *args, retries=3, delay=2, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return await func(*args, **kwargs)
            except discord.HTTPException as e:
                if e.status == 503:
                    pretty_log(
                        "warn",
                        f"HTTP 503 error on attempt {attempt}. Retrying in {delay}s...",
                        source="MessageCreateListener",
                    )
                    if attempt < retries:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise

    # 💜────────────────────────────────────────────
    #           👂 Message Listener Event
    # 💜────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            # 🚫 Ignore bots except PokéMeow, but allow webhooks
            if (
                message.author.bot
                and message.author.id != POKEMEOW_APPLICATION_ID
                and not message.webhook_id
            ):
                return

            # --- Market alert processing only---
            if (
                message.guild
                and message.guild.id == MAIN_SERVER_ID
                and message.channel.category_id == Categories.Market_Feed
            ):
                """pretty_log(
                    "debug",
                    f"Message caught: guild={message.guild.id if message.guild else None}, "
                    f"channel_parent={message.channel.parent_id}, "
                    f"author={message.author} ({message.author.id}), "
                    f"webhook_id={message.webhook_id}",
                )"""

                await process_market_alert_message(
                    self.bot, message, Categories.Market_Feed
                )

        except Exception as e:
            pretty_log(
                "critical",
                f"Unhandled exception in on_message: {e}",
                include_trace=True,
            )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
