import re
from datetime import datetime

import discord
from discord.ext import commands

from config.settings import POKEMEOW_APPLICATION_ID
from utils.db.schedule_db_func import upsert_user_schedule, delete_user_schedule
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member
from utils.cache.cache_list import timer_cache

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 Regex Patterns
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATCHBOT_RUN_PATTERN = re.compile(r"in \*\*(\d+)([hHmM])\*\*", re.IGNORECASE)
CATCHBOT_EMBED_PATTERN = re.compile(r"It will be back on .*?<t:(\d+):f>", re.IGNORECASE)
CHECKLIST_CB_PATTERN = re.compile(
    r"Your catch bot will be back on <t:(\d+):f>", re.IGNORECASE
)
CATCHBOT_RETURNED_PATTERN = re.compile(
    r":confetti_ball: \*\*Your catchbot returned with \d+ Pokemon!?\*\*",
    re.IGNORECASE,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 ;cl checklist embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_checklist_message(bot: commands.Bot, message: discord.Message):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    embed = message.embeds[0]
    if not embed or not embed.description:
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # 🔹 Must have catchbot setting and mode != off
    timers = timer_cache.get(member.id)
    if not timers:
        return None
    cb_setting = (timers.get("catchbot_setting") or "off").lower()
    if cb_setting == "off":
        return None

    m = CHECKLIST_CB_PATTERN.search(embed.description)
    if not m:
        return

    timestamp = int(m.group(1))
    if not timestamp:
        return

    # 🗂️ Save schedule
    result = await extract_and_save_catchbot_schedule(
        bot=bot, user=member, timestamp=timestamp
    )

    # 📅 React only if new schedule
    if result == "added":
        try:
            await message.reference.resolved.add_reaction("📅")
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"[CB CHECKLIST] Failed to add 📅 reaction: {e}",
                bot=bot,
            )

    pretty_log(
        tag="info",
        message=f"[CB CHECKLIST] Result={result} ts={timestamp} for {member.id}",
        bot=bot,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 ;cb embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_command_embed(bot: commands.Bot, message: discord.Message):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    embed = message.embeds[0]
    if not embed:
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # 🔹 Must have catchbot setting and mode != off
    timers = timer_cache.get(member.id)
    if not timers:
        return None
    cb_setting = (timers.get("catchbot_setting") or "off").lower()
    if cb_setting == "off":
        return None

    # 🔹 1. Try matching timestamp in description
    timestamp = None
    if embed.description:
        m = CATCHBOT_EMBED_PATTERN.search(embed.description)
        if m:
            timestamp = int(m.group(1))
            pretty_log(
                tag="embed",
                message=f"[CB EMBED] Found ts in description: {timestamp}",
                bot=bot,
            )

    # 🔹 2. If not found, try each field value
    if not timestamp:
        for field in embed.fields:
            if not field.value:
                continue
            m = CATCHBOT_EMBED_PATTERN.search(field.value)
            if m:
                timestamp = int(m.group(1))
                pretty_log(
                    tag="embed",
                    message=f"[CB EMBED] Found ts in field '{field.name}': {timestamp}",
                    bot=bot,
                )
                break

    # 🔹 3. If still not found, stop
    if not timestamp:
        return

    # 🗂️ Save schedule
    result = await extract_and_save_catchbot_schedule(
        bot=bot, user=member, timestamp=timestamp
    )

    # 📅 React only if new schedule
    if result == "added":
        try:
            await message.reference.resolved.add_reaction("📅")
        except Exception as e:
            pretty_log(
                tag="warn",
                message=f"[CB EMBED] Failed to add 📅 reaction: {e}",
                bot=bot,
            )

    pretty_log(
        tag="info",
        message=f"[CB EMBED] Result={result} ts={timestamp} for {member.name}",
        bot=bot,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 ;cb run
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_run_message(bot, message: discord.Message):
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        user = message.reference.resolved.author
        if not user:
            return None

        # 🔹 Must have catchbot setting and mode != off
        timers = timer_cache.get(user.id)
        if not timers:
            return None
        cb_setting = (timers.get("catchbot_setting") or "off").lower()
        if cb_setting == "off":
            return None

        content = message.content or ""
        run_match = CATCHBOT_RUN_PATTERN.search(content)
        if not run_match:
            return None

        value, unit = run_match.groups()
        value = int(value)
        seconds = value * (3600 if unit.lower() == "h" else 60)
        timestamp = int(message.created_at.timestamp()) + seconds

        # 🗂️ Save schedule
        result = await extract_and_save_catchbot_schedule(bot, user, timestamp)

        # 📅 React if new schedule added
        if result == "added":
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                pretty_log(
                    tag="warn",
                    message=f"[CB RUN] Failed to add 📅 reaction: {e}",
                    bot=bot,
                )

        pretty_log(
            tag="info",
            message=f"[CB RUN] Result={result} ts={timestamp} for {user.name}",
            bot=bot,
        )

    except Exception as e:
        pretty_log(
            tag="error", message=f"[CB RUN] Failed on {message.id}: {e}", bot=bot
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# cb return
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_return_message(bot, message: discord.Message):
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        user = message.reference.resolved.author
        if not user:
            return None

        # 🔹 Must have catchbot setting and mode != off
        timers = timer_cache.get(user.id)
        if not timers:
            return None
        cb_setting = (timers.get("catchbot_setting") or "off").lower()
        if cb_setting == "off":
            return None

        await delete_user_schedule(bot, user.id, "catchbot")

        # 🔹 Clear catchbot schedule from cache
        from utils.cache.schedule_cache import remove_schedule_cached

        remove_schedule_cached(user.id, "catchbot")

        pretty_log(
            tag="info",
            message=f"[CB RETURN] Cleared catchbot schedule for {user.name}",
            bot=bot,
        )
        return "deleted"

    except Exception as e:
        pretty_log(
            tag="error", message=f"[CB RETURN] Failed on {message.id}: {e}", bot=bot
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shared save logic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def extract_and_save_catchbot_schedule(
    bot, user: discord.User | discord.Member, timestamp: int
) -> str:
    """
    Upsert user's catchbot schedule and update cache.
    Returns: "added", "unchanged", or "failed"
    """
    pretty_log(
        tag="info",
        message=f"➡️ [CB SAVE] Entered extract_and_save_catchbot_schedule for {user.name} (ID: {user.id})",
        bot=bot,
    )
    try:
        # 🔹 Must have catchbot setting and mode != off
        timers = timer_cache.get(user.id)
        if not timers:
            return "failed"
        cb_setting = (timers.get("catchbot_setting") or "off").lower()
        if cb_setting == "off":
            pretty_log(
                tag="skip",
                message=f"[CB SAVE] Skipped for {user.name} → catchbot mode is OFF",
                bot=bot,
            )
            return "failed"

        # 🔎 Skip if schedule unchanged
        from utils.cache.schedule_cache import fetch_user_schedules_cached

        # Get current scheduled timestamp for catchbot
        user_schedules = await fetch_user_schedules_cached(bot, user.id)
        current_ts = None
        for schedule in user_schedules:
            if schedule["type"] == "catchbot":
                current_ts = schedule["scheduled_on"]
                break

        if current_ts == timestamp:
            pretty_log(
                tag="skip",
                message=f"[CB SAVE] Skipped for {user.name} → schedule unchanged ({timestamp})",
                bot=bot,
            )
            return "unchanged"

        # 💾 Write to DB - Delete existing then insert new
        await delete_user_schedule(bot, user.id, "catchbot")
        await upsert_user_schedule(
            bot=bot,
            user_id=user.id,
            user_name=user.name,
            type_="catchbot",
            scheduled_on=timestamp,
        )

        # 🗃️ Update cache - Remove old and fetch fresh
        from utils.cache.schedule_cache import (
            remove_schedule_cached,
            fetch_user_schedules_cached,
        )

        remove_schedule_cached(user.id, "catchbot")
        # Fetch updated schedules to refresh cache with new reminder_id
        await fetch_user_schedules_cached(bot, user.id)

        pretty_log(
            tag="info",
            message=f"[CB SAVE] Stored schedule {timestamp} for {user.name}",
            bot=bot,
        )
        return "added"

    except Exception as e:
        pretty_log(
            tag="error", message=f"[CB SAVE] Failed for {user.name}: {e}", bot=bot
        )
        return "failed"
