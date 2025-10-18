import re
from datetime import datetime
import time

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.settings import POKEMEOW_APPLICATION_ID
from utils.cache.cache_list import timer_cache, user_info_cache
from utils.db.user_info_db_func import set_user_info
from utils.db.schedule_db_func import (

    delete_user_schedule,
    fetch_user_schedule,
    update_scheduled_on,
    upsert_user_schedule,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

PATREON_QUEST_INFO_MAP = {
    "no_perks": {
        "max_quests": 3,
        "quest_interval_duration": 2 * 60 * 60,  # 2 hours in seconds
    },
    "common": {
        "max_quests": 3,
        "quest_interval_duration": 2 * 60 * 60,  # 2 hours in seconds
    },
    "uncommon": {
        "max_quests": 4,
        "quest_interval_duration": 2 * 60 * 60,  # 2 hours in seconds
    },
    "rare": {
        "max_quests": 5,
        "quest_interval_duration": 1 * 60 * 60,  # 1 hour in seconds
    },
    "superrare": {
        "max_quests": 5,
        "quest_interval_duration": 1 * 60 * 60,  # 1 hour in seconds
    },
    "legendary": {
        "max_quests": 5,
        "quest_interval_duration": 1 * 60 * 60,  # 1 hour in seconds
    },
    "shiny": {
        "max_quests": 5,
        "quest_interval_duration": 1 * 60 * 60,  # 1 hour in seconds
    },
    "golden": {
        "max_quests": 5,
        "quest_interval_duration": 1 * 60 * 60,  # 1 hour in seconds
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 ;cl checklist embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_quest_checklist_message(bot: commands.Bot, message: discord.Message):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    embed = message.embeds[0]
    if not embed or not embed.description:
        return

    embed_description = embed.description

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # Check user's quest timer settings
    user_timer = timer_cache.get(member.id)
    if not user_timer:
        return

    quest_timer_settings = user_timer.get("quest_settings")
    if quest_timer_settings == "off":
        return  # User has quest timers turned off

    if (
        ":black_medium_square: <:questreset:674490475377459200> Your next quest is available!"
        in embed.description
    ):
        # User's quest is ready, remove any existing schedule
        await delete_user_schedule(
            bot=bot,
            user_id=member.id,
            schedule_type="quest",
        )
        content = f"{Emojis.quest} {member.mention}, your next quest is available!"
        await message.channel.send(content)
        pretty_log(
            tag="quest",
            message=f"Deleted quest schedule for user {member.id} ({member.display_name}) as their quest is ready.",
            bot=bot,
        )
        return

    match = re.search(r"Your next quest is available <t:(\d+):R>", embed_description)
    quest_ready_timestamp = None
    if match:
        quest_ready_timestamp = int(match.group(1))

        # Look for existing schedule
        old_quest_schedule = await fetch_user_schedule(
            bot=bot,
            user_id=member.id,
            type_="quest",
        )
        if not old_quest_schedule:
            # No existing schedule, create a new one
            await upsert_user_schedule(
                bot=bot,
                user_id=member.id,
                user_name=member.name,
                type_="quest",
                scheduled_on=quest_ready_timestamp,
                channel_id=message.channel.id,
            )
            pretty_log(
                tag="quest",
                message=f"Created new quest schedule for user {member.id} ({member.display_name}) at timestamp {quest_ready_timestamp}.",
                bot=bot,
            )
        elif old_quest_schedule:
            # Check if existing schedule is the same
            if old_quest_schedule["scheduled_on"] != quest_ready_timestamp:
                # Update existing schedule with new timestamp
                await update_scheduled_on(
                    bot=bot,
                    user_id=member.id,
                    type_="quest",
                    new_scheduled_on=quest_ready_timestamp,
                )
                pretty_log(
                    tag="quest",
                    message=f"Updated quest schedule for user {member.id} ({member.display_name}) to new timestamp {quest_ready_timestamp}.",
                    bot=bot,
                )
                return
            else:
                pretty_log(
                    tag="quest",
                    message=f"Quest schedule for user {member.id} ({member.display_name}) is already up to date.",
                    bot=bot,
                )
                return
    else:
        return  # No timestamp found, do nothing

# ────────────────────────────────────────────
#   🎀 Count Current Quests from Embed Description
# ────────────────────────────────────────────
def count_current_quests(embed_description: str) -> int:
    """
    Counts the number of active quests in the embed description.
    Example: Each quest starts with '**Quest #N**:'
    """
    return len(re.findall(r"\*\*Quest #\d+\*\*:", embed_description))

# ────────────────────────────────────────────
#   🎀 Parse Footer Timer to Unix Seconds
# ────────────────────────────────────────────
def parse_footer_timer_to_unix_seconds(footer_text: str) -> int | None:
    """
    Parses a timer string like 'Next quest in: 1 H 59 M 59 S' and returns the future Unix timestamp.
    """
    match = re.search(
        r"Next quest in:\s*((?:(\d+)\s*H)?\s*((\d+)\s*M)?\s*((\d+)\s*S)?)", footer_text
    )
    if not match:
        return None

    hours = int(match.group(2) or 0)
    minutes = int(match.group(4) or 0)
    seconds = int(match.group(6) or 0)
    total_seconds = hours * 3600 + minutes * 60 + seconds

    now_unix = int(time.time())
    return now_unix + total_seconds


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎀 ;quest embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_quest_embed(bot, message: discord.Message):

    if message.author.id != POKEMEOW_APPLICATION_ID:
        return
    embed = message.embeds[0]

    if not embed or not embed.description:
        return

    embed_description = embed.description

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # Check user's quest timer settings
    user_timer = timer_cache.get(member.id)
    if not user_timer:
        return
    quest_timer_settings = user_timer.get("quest_settings")
    if quest_timer_settings == "off":
        return  # User has quest timers turned off

    # Check footer
    embed_footer_text = embed.footer.text if embed.footer else ""
    if "Your next quest is available!" in embed_footer_text:
        # User's quest is ready, remove any existing schedule
        user_quest_schedule = await fetch_user_schedule(
            bot=bot,
            user_id=member.id,
            type_="quest",
        )
        if not user_quest_schedule:
            return

        else:
            await delete_user_schedule(
                bot=bot,
                user_id=member.id,
                schedule_type="quest",
            )
            content = f"{Emojis.quest} {member.mention}, your next quest is available!"
            await message.channel.send(content)
            pretty_log(
                tag="quest",
                message=f"Deleted quest schedule for user {member.id} ({member.display_name}) as their quest is ready.",
                bot=bot,
            )
            return

    # Get user's patreon perk level
    user_info = user_info_cache.get(member.id)
    if not user_info:
        #Upsert user info in db and cache if not present
        await set_user_info(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
        )
        return
    patreon_tier = user_info.get("patreon_tier")
    if not patreon_tier:
        content = f"Please tell me your Patreon rank by using the command `;perks` or `;pro`"
        await message.channel.send(content)
        pretty_log(
            tag="quest",
            message=f"User {member.id} ({member.display_name}) has no patreon perk set.",
        )
        return

    # Extract footer timer
    footer_text = embed.footer.text if embed.footer else ""
    next_quest_unix = parse_footer_timer_to_unix_seconds(footer_text)
    if not next_quest_unix:
        pretty_log(
            tag="quest",
            message=f"Could not extract next quest timer from footer: {footer_text}",
        )
        return
    # Check for existing schedule
    old_quest_schedule = await fetch_user_schedule(
        bot=bot,
        user_id=member.id,
        type_="quest",
    )

    if not old_quest_schedule:
        # No existing schedule, create a new one
        await upsert_user_schedule(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            type_="quest",
            scheduled_on=next_quest_unix,
            channel_id=message.channel.id,
        )
        pretty_log(
            tag="quest",
            message=f"Created new quest schedule for user {member.id} ({member.display_name}) at timestamp {next_quest_unix}.",
            bot=bot,
        )
        return
    elif old_quest_schedule:
        # Check if existing schedule is the same
        if old_quest_schedule["scheduled_on"] != next_quest_unix:
            # Update existing schedule with new timestamp
            await update_scheduled_on(
                bot=bot,
                user_id=member.id,
                type_="quest",
                new_scheduled_on=next_quest_unix,
            )
            pretty_log(
                tag="quest",
                message=f"Updated quest schedule for user {member.id} ({member.display_name}) to new timestamp {next_quest_unix}.",
                bot=bot,
            )
            return
        else:
            pretty_log(
                tag="quest",
                message=f"Quest schedule for user {member.id} ({member.display_name}) is already up to date.",
                bot=bot,
            )
            return

# ────────────────────────────────────────────
#   🎀 Handle Quest Complete Message
# ────────────────────────────────────────────
async def handle_quest_complete_message(bot, message: discord.Message):
    """
    Handles quest completion messages to update or delete quest schedules.
    """

    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    message_content = message.content

    if not message_content:
        return

    # Get the username from the message
    match = re.search(
        r":notepad_spiral:\s+\*\*(.+?)\*\* completed the quest", message_content
    )
    if not match:
        return
    raw_username = match.group(1)

    # Get the member object from the guild
    guild = message.guild
    member = discord.utils.find(
        lambda m: m.name == raw_username or m.display_name == raw_username, guild.members
    )
    if not member:
        return

    member_id = member.id

    # Check user's quest timer settings
    user_timer = timer_cache.get(member_id)
    if not user_timer:
        return

    quest_timer_settings = user_timer.get("quest_settings")
    if quest_timer_settings == "off":
        return  # User has quest timers turned off

    # Check user's patreon perk level
    user_info = user_info_cache.get(member_id)
    if not user_info:
        # Upsert user info in db and cache if not present
        await set_user_info(
            bot=bot,
            user_id=member_id,
            user_name=member.name,
        )
        return
    patreon_tier = user_info.get("patreon_tier")
    if not patreon_tier:
        content = f"Please tell me your Patreon rank by using the command `;perks` or `;pro`"
        await message.channel.send(content)
        pretty_log(
            tag="quest",
            message=f"User {member_id} ({member.display_name}) has no patreon perk set.",
        )
        return

    quest_info = PATREON_QUEST_INFO_MAP.get(patreon_tier)
    quest_interval_duration = quest_info["quest_interval_duration"]

    # Check for existing schedule
    old_quest_schedule = await fetch_user_schedule(
        bot=bot,
        user_id=member_id,
        type_="quest",
    )
    if old_quest_schedule:
        # Do nothing if schedule exists, as next quest time is unknown
        return
    elif not old_quest_schedule:
        # Create a new schedule with the interval duration added to current time
        next_quest_unix = int(time.time()) + quest_interval_duration
        await upsert_user_schedule(
            bot=bot,
            user_id=member_id,
            user_name=member.name,
            type_="quest",
            scheduled_on=next_quest_unix,
            channel_id=message.channel.id,
        )
        pretty_log(
            tag="quest",
            message=f"Created new quest schedule for user {member_id} ({member.display_name}) at timestamp {next_quest_unix} after quest completion.",
            bot=bot,
        )
        return