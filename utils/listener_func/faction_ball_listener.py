import re

import discord

from config.faction_data import get_faction_by_emoji
from utils.cache.cache_list import daily_faction_ball_cache, user_info_cache
from utils.db.daily_faction_ball_db import fetch_all_faction_balls, update_faction_ball
from utils.db.user_info_db_func import set_user_info, update_faction
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member


# 🟣────────────────────────────────────────────
# [🎯 FUNCTION] Faction Ball Listener
# 🟣────────────────────────────────────────────
async def extract_faction_ball_from_daily(bot, message: discord.Message):
    """Listens to PokéMeow's daily message for faction ball info."""

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_description = embed.description or ""
    if not embed_description or "daily streak" not in embed_description:
        return

    # Regex to match: <:team_logo:ID> **|** Your Faction's daily ball-type is <:ball_emoji:ID> BallName
    match = re.search(
        r"(<:team_logo:\d+>) \*\*\|\*\* Your Faction's daily ball-type is (<:[^:]+:\d+>) (\w+ball)",
        embed.description,
    )
    if not match:
        return

    faction_team_emoji = match.group(1)
    daily_ball_emoji = match.group(2)
    daily_ball = match.group(3)
    faction = get_faction_by_emoji(faction_team_emoji)
    daily_ball = daily_ball.lower()

    if not faction:
        pretty_log(
            tag="error",
            message=f"Could not identify faction from emoji {faction_team_emoji}",
            bot=bot,
        )
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    member_id = member.id
    member_name = member.name

    # Check if there user has a faction or not
    member_info = user_info_cache.get(member_id)
    if not member_info and not member_info.get("faction"):
        # New user upsert in db (Db will also update cache)
        await set_user_info(
            bot,
            user_id=member_id,
            user_name=member_name,
            faction=faction,
            patreon_tier=None,
        )
    elif member_info and not member_info.get("faction"):
        # Has row but no faction set (Update db and cache)
        await update_faction(
            bot,
            user=member,
            faction=faction,
        )

    # Check if there is a ball already set for that faction
    latest_ball = daily_faction_ball_cache.get(faction)
    if latest_ball == daily_ball:
        # No change
        return
    elif not latest_ball:
        # No entry yet, insert new in db and cache
        await update_faction_ball(bot, faction, daily_ball)

# 🍥──────────────────────────────────────────────
#   Extract Faction Ball from Faction Command
# 🍥──────────────────────────────────────────────
async def extract_faction_ball_from_fa(bot, message: discord.Message):
    # Extract faction from author line (e.g. "Team Magma — Headquarters")
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    faction = None
    if not embed.author or not embed.author.name:
        return

    author_match = re.search(r"Team (\w+)", embed.author.name)
    if not author_match:
        return

    faction = author_match.group(1)
    faction = faction.lower()

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    # Check if there is a daily ball for that faction and if member has a faction
    daily_faction_ball = daily_faction_ball_cache.get(faction)
    member_info = user_info_cache.get(member.id)
    member_faction = member_info.get("faction") if member_info else None
    if not member_info:
        # upsert
        await set_user_info(
            bot,
            user_id=member.id,
            user_name=member.name,
            faction=faction,
            patreon_tier=None,
        )
    elif not member_faction:
        # update
        await update_faction(
            bot,
            user=member,
            faction=faction,
        )
    if daily_faction_ball:
        return # Already have a ball set, do nothing

    # Extract daily ball from description line (e.g. "<:greatball:...> **Today's target Pokemon are**")
    daily_ball = None
    if not embed.description:
        return

    ball_match = re.search(
        r"<:([a-zA-Z0-9_]+):\d+>\s+\*\*Today's target Pokemon are\*\*",
        embed.description,
    )
    if not ball_match:
        return
    daily_ball = ball_match.group(1)

    # Update db and cache
    await update_faction_ball(bot, faction, daily_ball)
