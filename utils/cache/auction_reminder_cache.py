from typing import Dict

import discord

from utils.cache.cache_list import auction_reminder_cache
from utils.db.auction_reminder_db import fetch_all_auction_reminders
from utils.logs.pretty_log import pretty_log


# 💜────────────────────────────────────────────
#    🕰 Auction Reminder Cache Loader 🕰
# 💜────────────────────────────────────────────
async def load_auction_reminder_cache(bot):
    """
    Loads auction reminders from the database into the global cache.
    """
    auction_reminder_cache.clear()
    try:
        reminders = await fetch_all_auction_reminders(bot)
        for reminder in reminders:
            ends_on = reminder["ends_on"]
            user_id = reminder["user_id"]
            user_name = reminder["user_name"]
            alarm_set = reminder["alarm_set"]
            auction_reminder_cache[(ends_on, user_id)] = {
                "ends_on": ends_on,
                "user_id": user_id,
                "user_name": user_name,
                "alarm_set": alarm_set,
            }
        pretty_log(
            tag="cache",
            message=f"Loaded {len(auction_reminder_cache)} auction reminders into cache.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to load auction reminders into cache: {e}",
        )


def upsert_auction_reminder_cache(
    ends_on: int, user_id: int, user_name: str, alarm_set: bool
):
    """
    Inserts or updates an auction reminder in the global cache.
    """
    auction_reminder_cache[(ends_on, user_id)] = {
        "ends_on": ends_on,
        "user_id": user_id,
        "user_name": user_name,
        "alarm_set": alarm_set,
    }
    pretty_log(
        tag="cache",
        message=f"Upserted auction reminder in cache: ends_on={ends_on}, user_id={user_id}, user_name={user_name}, alarm_set={alarm_set}",
    )


def update_auction_reminder_cache(ends_on: int, user_id: int, alarm_set: bool):
    """
    Updates the alarm_set status of an auction reminder in the global cache.
    """
    key = (ends_on, user_id)
    if key in auction_reminder_cache:
        auction_reminder_cache[key]["alarm_set"] = alarm_set
        pretty_log(
            tag="cache",
            message=f"Updated auction reminder in cache: ends_on={ends_on}, user_id={user_id}, alarm_set={alarm_set}",
        )
    else:
        pretty_log(
            tag="warn",
            message=f"Attempted to update non-existent auction reminder in cache: ends_on={ends_on}, user_id={user_id}",
        )


def remove_auction_reminder_cache(ends_on: int, user_id: int):
    """
    Removes an auction reminder from the global cache.
    """
    key = (ends_on, user_id)
    if key in auction_reminder_cache:
        del auction_reminder_cache[key]
        pretty_log(
            tag="cache",
            message=f"Removed auction reminder from cache: ends_on={ends_on}, user_id={user_id}",
        )
    else:
        pretty_log(
            tag="warn",
            message=f"Attempted to remove non-existent auction reminder from cache: ends_on={ends_on}, user_id={user_id}",
        )


def remove_all_auction_reminders_cache():
    """
    Clears all auction reminders from the global cache.
    """
    auction_reminder_cache.clear()
    pretty_log(
        tag="cache",
        message="Cleared all auction reminders from cache.",
    )


def is_timestamp_more_than_5_hours_away_cache(timestamp: int, user_id: int) -> bool:
    """
    Returns True if the given timestamp is more than 5 hours away from all ends_on values in the global auction_reminder_cache for the given user_id.
    :param timestamp: The timestamp to check.
    :param user_id: The user ID to check for.
    :return: True if timestamp is more than 5 hours away from all ends_on keys for the user, else False.
    """
    five_hours = 5 * 60 * 60  # 5 hours in seconds
    for (ends_on, uid), reminder in auction_reminder_cache.items():
        if uid == user_id:
            if abs(ends_on - timestamp) <= five_hours:
                return False
    return True
