# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.settings import *
from utils.listener_func.market_alert_listener import process_market_alert_message
from utils.listener_func.market_purchase_listener import get_purchased_pokemon
from utils.logs.pretty_log import pretty_log
from utils.listener_func.single_trade_listener import handle_single_trade_message
from utils.listener_func.multi_trade_listener import handle_multitrade_message

purchase_trigger = "<:checkedbox:752302633141665812> Successfully purchased"
multi_trade_trigger = "<:checkedbox:752302633141665812> Trade complete! :handshake:"

# 💜────────────────────────────────────────────
#           🧩 Message Create Listener Cog
# 💜────────────────────────────────────────────
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

            # 💖────────────────────────────────────────────
            #           🛒 Purchase Processing Only
            # 💖────────────────────────────────────────────
            if message.content and purchase_trigger in message.content:
                await get_purchased_pokemon(self.bot, message)

            # 💖────────────────────────────────────────────
            #           🤝 Single Trade Processing Only
            # 💖────────────────────────────────────────────
            if message.content and ":handshake:" in message.content:
                await handle_single_trade_message(self.bot, message)

            # 💖────────────────────────────────────────────
            #           🤝 Multi Trade Processing Only
            # 💖────────────────────────────────────────────
            if message.content and multi_trade_trigger in message.content:
                await handle_multitrade_message(self.bot, message)

            # 💖────────────────────────────────────────────
            #           📢 Market Alert Processing Only
            # 💖────────────────────────────────────────────
            if (
                message.guild
                and message.guild.id == MAIN_SERVER_ID
                and message.channel.category_id == Categories.Market_Feed
            ):

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
