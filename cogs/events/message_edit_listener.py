# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.settings import *
from utils.listener_func.auction_command_listener import auction_command_listener
from utils.listener_func.faction_hunt_alert import faction_hunt_alert
from utils.listener_func.fish_rarity_embed import fish_rarity_embed
from utils.listener_func.quest_listener import handle_quest_complete_message
from utils.listener_func.rarespawn.catch_and_fish import (
    catch_and_fish_message_rare_spawn_handler,
)
from utils.listener_func.tcg_inv import parse_tcg_inventory_embed
from utils.logs.pretty_log import pretty_log

auction_command_trigger = "Auctions on this page"
RARE_SPAWN_TRIGGERS = ["You caught a", "broke out of the", "ran away"]
FISHING_COLOR = 0x87CEFA


class MessageEditListener(commands.Cog):
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
                        tag="warn",
                        message=f"HTTP 503 error on attempt {attempt}. Retrying in {delay}s...",
                    )
                    if attempt < retries:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise

    # 💜────────────────────────────────────────────
    #           👂 Message Edit Listener Event
    # 💜────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        try:
            # 🚫 Ignore bots except PokeMeow, but allow webhooks
            if (
                after.author.bot
                and after.author.id != POKEMEOW_APPLICATION_ID
                and not after.webhook_id
            ):
                return

            # Safety check for embeds
            if not after.embeds:
                return

            embed = after.embeds[0]
            embed_desc = embed.description if embed else ""
            embed_title = embed.title if embed else ""
            embed_footer_text = (
                embed.footer.text if embed.footer and embed.footer.text else ""
            )

            # 💜────────────────────────────────────────────
            #     🎣  Fish Rarity Embed Handler
            # 💜────────────────────────────────────────────
            if embed_desc and "fished a wild" in embed_desc:
                await fish_rarity_embed(self.bot, before, after)

            # 💜────────────────────────────────────────────
            #     Rare Spawn Catch and Fish Handler
            # 💜────────────────────────────────────────────
            if embed_desc and any(
                trigger in embed_desc for trigger in RARE_SPAWN_TRIGGERS
            ):
                await catch_and_fish_message_rare_spawn_handler(self.bot, before, after)
            # 💜────────────────────────────────────────────
            #           🟣 Faction Hunt Alerts
            # 💜────────────────────────────────────────────
            if after.embeds:
                desc = after.embeds[0].description
                color = after.embeds[0].color
                if (
                    desc
                    and "<:team_logo:" in desc
                    and "fished a wild" in desc
                    and (
                        color == FISHING_COLOR
                        or getattr(color, "value", None) == FISHING_COLOR
                    )
                ):
                    pretty_log(
                        "info",
                        f"Detected faction ball alert in fish embed",
                        label="🛡️ FACTION BALL ALERT",
                        bot=self.bot,
                    )
                    await faction_hunt_alert(bot=self.bot, before=before, after=after)
            # 💜────────────────────────────────────────────
            #        🟣 TCG Inventory Embed Parser
            # 💜────────────────────────────────────────────
            if after.embeds:
                first_embed_title = after.embeds[0].title or ""
                if first_embed_title and "tcg inventory" in first_embed_title.lower():
                    pretty_log(
                        "info",
                        f"Detected TCG Inventory Embed Edit",
                        label="🃏 TCG INVENTORY EDIT",
                        bot=self.bot,
                    )
                    await parse_tcg_inventory_embed(
                        message=after,
                    )
            # 💜────────────────────────────────────────────
            #        🟣 Auction Command Listener
            # 💜────────────────────────────────────────────
            if after.embeds:
                if (
                    after.embeds[0].footer
                    and auction_command_trigger in after.embeds[0].footer.text
                ):
                    pretty_log(
                        "info",
                        f"Detected Auction Command Embed Edit",
                        label="🏷️ AUCTION COMMAND EDIT",
                        bot=self.bot,
                    )
                    await auction_command_listener(self.bot, before, after)
            # 💜────────────────────────────────────────────
            #        📝 Quest Complete Processing Only
            # 💜────────────────────────────────────────────
            if (
                after.content
                and ":notepad_spiral" in after.content
                and "completed the quest" in after.content
            ):
                await handle_quest_complete_message(self.bot, after)
        except Exception as e:
            pretty_log(
                tag="critical",
                message=f"Unhandled exception in on_message_edit: {e}",
            )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEditListener(bot))
