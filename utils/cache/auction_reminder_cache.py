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
    # Clear existing cache
    auction_reminder_cache.clear()
    try:
        reminders = await fetch_all_auction_reminders(bot)
        for reminder in reminders:
            ends_on = reminder["ends_on"]
            alarm_set = reminder["alarm_set"]
            auction_reminder_cache[ends_on] = alarm_set
        pretty_log(
            tag="cache",
            message=f"Loaded {len(auction_reminder_cache)} auction reminders into cache.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to load auction reminders into cache: {e}",
        )


def upsert_auction_reminder_cache(ends_on: int, alarm_set: bool):
    """
    Inserts or updates an auction reminder in the global cache.
    """
    auction_reminder_cache[ends_on] = alarm_set
    pretty_log(
        tag="cache",
        message=f"Upserted auction reminder in cache: ends_on={ends_on}, alarm_set={alarm_set}",
    )


def update_auction_reminder_cache(ends_on: int, alarm_set: bool):
    """
    Updates the alarm_set status of an auction reminder in the global cache.
    """
    if ends_on in auction_reminder_cache:
        auction_reminder_cache[ends_on] = alarm_set
        pretty_log(
            tag="cache",
            message=f"Updated auction reminder in cache: ends_on={ends_on}, alarm_set={alarm_set}",
        )
    else:
        pretty_log(
            tag="warn",
            message=f"Attempted to update non-existent auction reminder in cache: ends_on={ends_on}",
        )


def remove_auction_reminder_cache(ends_on: int):
    """
    Removes an auction reminder from the global cache.
    """
    if ends_on in auction_reminder_cache:
        del auction_reminder_cache[ends_on]
        pretty_log(
            tag="cache",
            message=f"Removed auction reminder from cache: ends_on={ends_on}",
        )
    else:
        pretty_log(
            tag="warn",
            message=f"Attempted to remove non-existent auction reminder from cache: ends_on={ends_on}",
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


def is_timestamp_more_than_5_hours_away_cache(
    cache: Dict[int, bool], timestamp: int
) -> bool:
    """
    Returns True if the given timestamp is more than 5 hours away from all ends_on values in the cache.
    :param cache: Dictionary with ends_on as keys and alarm_set as values.
    :param timestamp: The timestamp to check.
    :return: True if timestamp is more than 5 hours away from all ends_on keys, else False.
    """
    five_hours = 5 * 60 * 60  # 5 hours in seconds
    for ends_on in cache.keys():
        if abs(ends_on - timestamp) <= five_hours:
            return False
    return True
