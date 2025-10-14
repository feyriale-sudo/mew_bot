import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.settings import POKEMEOW_APPLICATION_ID, FISH_TIMER
from utils.cache.cache_list import timer_cache  # 💜 import your cache
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member


# 🗂 Track scheduled "command ready" tasks to avoid duplicates
fish_ready_tasks = {}


# 💜────────────────────────────────────────────
#   Function: detect_pokemeow_reply
#   Handles Pokemon timer notifications per user settings
# 💜────────────────────────────────────────────
async def fish_timer_handler(message: discord.Message):
    """
    Triggered on any message.
    Handles Fish ready notifications depending on user's timer cache settings:
      - off → ignore
      - on → ping them in channel
      - on w/o pings → send message w/o mention
    """
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        member = await get_pokemeow_reply_member(message)
        if not member:
            return

        # -------------------------------
        # 💜 Check timer_cache settings
        # -------------------------------
        user_settings = timer_cache.get(member.id)
        if not user_settings:
            return

        setting = (user_settings.get("fish_setting") or "off").lower()
        if setting == "off":
            return

        # Cancel previous ready task if any
        if member.id in fish_ready_tasks and not fish_ready_tasks[member.id].done():
            fish_ready_tasks[member.id].cancel()

        # Schedule behavior depending on setting
        async def notify_ready():
            # 💜────────────────────────────────────────────
            #   Fish Timer Notification Task
            # 💜────────────────────────────────────────────
            try:
                await asyncio.sleep(FISH_TIMER)

                if setting == "on":
                    await message.channel.send(
                        f"{Emojis.fish_spawn} {member.mention}, your </fish spawn:1015311084812501026> command is ready! "
                    )  # TODO update with skaia's emojis
                elif setting == "on_no_pings":
                    await message.channel.send(
                        f"{Emojis.fish_spawn} **{member.display_name}**, your </fish spawn:1015311084812501026> command is ready!"
                    )

            except asyncio.CancelledError:
                # 💙 [CANCELLED] Scheduled ready notification cancelled
                pretty_log(
                    tag="info",
                    message=f"Cancelled scheduled ready notification for {member}",
                )
            except Exception as e:
                # 💜 [MISSED] Timer ran correctly but message failed
                # Trackable: include member ID and username
                pretty_log(
                    tag="error",
                    message=(
                        f"Missed Pokemon timer notification for {member} "
                        f"(ID: {member.id}). Timer ran correctly but message failed: {e}"
                    ),
                )

        fish_ready_tasks[member.id] = asyncio.create_task(notify_ready())

    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in detect_pokemeow_reply: {e}",
        )
