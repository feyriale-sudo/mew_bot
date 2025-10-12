# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio
import re

import discord
from discord.ext import commands

from config.settings import *
from utils.listener_func.battle_timer import battle_timer_handler
from utils.listener_func.catchbot_listener import (
    handle_cb_checklist_message,
    handle_cb_command_embed,
    handle_cb_return_message,
    handle_cb_run_message,
)
from utils.listener_func.dex_listener import dex_message_handler
from utils.listener_func.fish_timer import fish_timer_handler
from utils.listener_func.market_alert_listener import process_market_alert_message
from utils.listener_func.market_purchase_listener import get_purchased_pokemon
from utils.listener_func.multi_trade_listener import handle_multitrade_message
from utils.listener_func.pokemon_timer import pokemon_timer_handler
from utils.listener_func.rarespawn.egg_hatch_rs import egg_rarespawn_handler
from utils.listener_func.rarespawn.swap_rare_spawn import swap_rarespawn_handler
from utils.listener_func.single_trade_listener import handle_single_trade_message
from utils.logs.pretty_log import pretty_log

# 💜────────────────────────────────────────────
#           🎯 Message Content Triggers
# 💜────────────────────────────────────────────
purchase_trigger = "<:checkedbox:752302633141665812> Successfully purchased"
multi_trade_trigger = "<:checkedbox:752302633141665812> Trade complete! :handshake:"
dex_trigger = ":dna: **Evolution line**"
cb_return_trigger = ":robot: I have returned with some Pokemon for you!"
cb_command_embed_trigger = (
    ":battery: Your CatchBot is currently catching Pokemon for you!"
)
cb_checklist_trigger = "View your event checklist with ;e cl"
CATCHBOT_SPENT_PATTERN = re.compile(
    r"You spent <:[^:]+:\d+> \*\*[\d,]+ PokeCoins\*\* to run your catch bot\.",
    re.IGNORECASE,
)


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
            first_embed = message.embeds[0] if message.embeds else None
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
            #           🧬 Dex Processing Only
            # 💖────────────────────────────────────────────
            if message.embeds and message.embeds[0]:
                embed = message.embeds[0]
                embed_description = embed.description
                if embed_description and dex_trigger in embed_description:
                    await dex_message_handler(self.bot, message)
            # 💖────────────────────────────────────────────
            #           🐣 Egg Hatch Rare Spawn Processing Only
            # 💖────────────────────────────────────────────
            # User hatched an Egg! in author text
            if (
                message.embeds
                and message.embeds[0]
                and message.content
                and message.embeds[0].author
                and "hatched an Egg!" in (message.embeds[0].author.name or "")
                and "just hatched a" in message.content
            ):
                await egg_rarespawn_handler(self.bot, message)

            # 💖────────────────────────────────────────────
            #           🔄 Swap Rare Spawn Processing Only
            # 💖────────────────────────────────────────────
            if (
                message.embeds
                and message.embeds[0]
                and message.content
                and message.embeds[0].author
                and "PokeMeow Swaps" in (message.embeds[0].author.name or "")
                and (
                    "received:" in message.content
                    or "from a swap" in message.content.lower()
                )
            ):
                await swap_rarespawn_handler(self.bot, message)
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
            # 💜────────────────────────────────────────────
            #           ⏲️ Pokemon Timer Processing Only
            # 💜────────────────────────────────────────────
            if message.embeds and message.embeds[0]:
                embed = message.embeds[0]
                embed_description = embed.description if embed else None
                if embed_description and "found a wild" in embed_description:
                    await pokemon_timer_handler(message)
            # 💜────────────────────────────────────────────
            #           🎣 Fish Timer Processing Only
            # 💜────────────────────────────────────────────
            if message.embeds and message.embeds[0]:
                embed = message.embeds[0]
                embed_description = embed.description if embed else None
                if (
                    embed_description
                    and "cast a" in embed_description
                    and "into the water" in embed_description
                ):
                    await fish_timer_handler(message)
            # 💜────────────────────────────────────────────
            #           ⚔️ Battle Timer Processing Only
            # 💜────────────────────────────────────────────
            if message.embeds and message.embeds[0]:
                await battle_timer_handler(self.bot, message)

            # 💜────────────────────────────────────────────
            #           🤖 CatchBot Processing Only
            # 💜────────────────────────────────────────────
            if message.content:
                # 1️⃣ CatchBot return text
                if cb_return_trigger.lower() in message.content.lower():
                    pretty_log(
                        "info",
                        f"Matched CatchBot return trigger | Message ID: {message.id} | Channel: {message.channel.name}",
                    )
                    await handle_cb_return_message(bot=self.bot, message=message)

                # 2️⃣ CatchBot run message
                elif CATCHBOT_SPENT_PATTERN.search(message.content):
                    pretty_log(
                        "info",
                        f"Matched CatchBot spent pattern | Message ID: {message.id} | Channel: {message.channel.name}",
                    )
                    await handle_cb_run_message(bot=self.bot, message=message)

            # 3️⃣ CatchBot embeds
            if first_embed:

                # 🔹 Check fields
                for field in first_embed.fields:
                    name = field.name.lower() if field.name else ""
                    value = field.value.lower() if field.value else ""

                    if (
                        cb_command_embed_trigger.lower() in name
                        or cb_command_embed_trigger.lower() in value
                    ):
                        pretty_log(
                            "embed",
                            f"Matched CatchBot command trigger in embed field: {field.name}",
                        )
                        await handle_cb_command_embed(bot=self.bot, message=message)
                        break

                # 🔹 Check footer for ;cl command
                if first_embed.footer and first_embed.footer.text:
                    footer_text = first_embed.footer.text.lower()
                    if cb_checklist_trigger.lower() in footer_text:
                        pretty_log(
                            "embed",
                            f"Matched CatchBot checklist trigger in embed footer: {footer_text}",
                        )
                        await handle_cb_checklist_message(
                            bot=self.bot, message=message
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
