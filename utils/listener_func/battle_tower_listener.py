import re

import discord

from config.aesthetic import Emojis
from utils.cache.cache_list import battle_tower_cache
from utils.db.battletower_db import register_battletower_user
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import (
    get_command_user,
    get_pokemeow_reply_member,
)

BATTLE_TOWER_NPC_IDS = [400, 401, 402, 403, 404, 405, 406, 407]
BATTLE_TOWER_NPC_NAME = [
    "battletower_clerk",
    "battletower_kid",
    "battletower_grandpa",
    "battletower_sage",
    "battletower_officer",
    "battletower_master_bianca",
    "battletower_master_rood",
    "battletower_master_buck",
]


def extract_battletower_npc_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the battletower NPC name (e.g., 'battletower_kid') from the embed description,
    but only if it appears after the word 'challenged'.
    Returns the NPC name as a string, or None if not found.
    """
    if not embed or not embed.description:
        return None
    # Find the word 'challenged' and search for the first emoji after it
    challenged_idx = embed.description.find("challenged")
    if challenged_idx == -1:
        return None
    after_challenged = embed.description[challenged_idx:]
    match = re.search(r"<:([a-zA-Z0-9_]+):[0-9]+>", after_challenged)
    if match:
        return match.group(1)
    return None


def extract_current_floor_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the value of the 'Current floor' field from a discord.Embed object.
    Returns the field value (e.g., 'Floor 1') or None if not found.
    """
    for field in embed.fields:
        if field.name.strip().lower() == "current floor":
            return field.value.strip()
    return None


# 🍡──────────────────────────────────────────────
#   Battle Tower Listener Functions
# 🍡──────────────────────────────────────────────
async def bt_register_listener(bot, message: discord.Message):
    """Listener for Battle Tower registration command."""

    member = await get_pokemeow_reply_member(message)
    if not member:
        # Get the command user
        member = await get_command_user(message)
        if not member:
            return  # Unable to determine the user

    user_id = member.id
    user_name = member.name
    # Check if member is in battle tower cache
    bt_user_info = battle_tower_cache.get(user_id)
    if bt_user_info:
        pretty_log(
            tag="info",
            message=f"User {user_name} ({user_id}) is already registered for Battle Tower.",
            bot=bot,
        )
        return

    await register_battletower_user(bot, user_id, user_name)
    pretty_log(
        tag="info",
        message=f"Registered user {user_name} ({user_id}) for Battle Tower.",
        bot=bot,
    )
    await message.reference.resolved.add_reaction(Emojis.sched_react)


async def bt_command_listener(bot, message: discord.Message):
    """Listener for Battle Tower command messages."""
    # Get member
    member = await get_pokemeow_reply_member(message)
    if not member:
        # Get the command user
        member = await get_command_user(message)
        if not member:
            return
    user_id = member.id
    user_name = member.name

    # Check if user is registered
    bt_user_info = battle_tower_cache.get(user_id)
    if bt_user_info:
        pretty_log(
            tag="info",
            message=f"User {user_name} ({user_id}) invoked Battle Tower command and is already registered.",
            bot=bot,
        )
        return

    # Check current floor from embed
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    current_floor = extract_current_floor_from_embed(embed)
    if not current_floor:
        return
    pretty_log(
        tag="info",
        message=f"User {user_name} ({user_id}) current floor extracted: {current_floor}",
        bot=bot,
    )
    if current_floor.lower() == "not registered":
        pretty_log(
            tag="info",
            message=f"User {user_name} ({user_id}) is not registered in Battle Tower.",
            bot=bot,
        )
        return  # User is not registered in Battle Tower

    # Register the user
    await register_battletower_user(bot, user_id, user_name)
    pretty_log(
        tag="info",
        message=f"Registered user {user_name} ({user_id}) for Battle Tower via command listener.",
        bot=bot,
    )
    await message.reference.resolved.add_reaction(Emojis.sched_react)
