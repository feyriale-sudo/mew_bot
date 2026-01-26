# SQL SCRIPT
"""CREATE TABLE auction_reminders (
    ends_on BIGINT PRIMARY KEY,
    alarm_set BOOLEAN
);"""

import asyncio

from utils.db.get_pg_pool import get_pg_pool
from utils.logs.pretty_log import pretty_log


async def is_timestamp_more_than_5_hours_away(bot, timestamp: int) -> bool:
    """
    Returns True if the given timestamp is more than 5 hours away from all ends_on values in the DB.
    Accepts bot as the first argument to use bot.pg_pool for DB connection.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            query = "SELECT ends_on FROM auction_reminders"
            rows = await conn.fetch(query)
            five_hours = 5 * 60 * 60  # 5 hours in seconds
            for row in rows:
                if abs(row["ends_on"] - timestamp) <= five_hours:
                    return False
            return True
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to check timestamp distance: {e}",
        )
        return False


# Example usage (for testing):
# asyncio.run(is_timestamp_more_than_5_hours_away(1700000000))
# Returns True if no ends_on is within 5 hours of 1700000000


async def upsert_auction_reminder(bot, ends_on: int, alarm_set: bool):
    """
    Inserts or updates an auction reminder in the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO auction_reminders (ends_on, alarm_set)
                VALUES ($1, $2)
                ON CONFLICT (ends_on) DO UPDATE SET alarm_set = $2
                """,
                ends_on,
                alarm_set,
            )
        pretty_log(
            tag="db",
            message=f"Upserted auction reminder for ends_on {ends_on} with alarm_set={alarm_set}.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert auction reminder for ends_on {ends_on}: {e}",
        )
async def fetch_auction_reminder(bot, ends_on: int):
    """
    Fetches an auction reminder by ends_on from the database.
    Returns a dictionary with keys 'ends_on' and 'alarm_set', or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT ends_on, alarm_set FROM auction_reminders WHERE ends_on = $1",
                ends_on,
            )
            if row:
                return {"ends_on": row["ends_on"], "alarm_set": row["alarm_set"]}
            else:
                return None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch auction reminder for ends_on {ends_on}: {e}",
        )
        return None

async def update_auction_reminder_alarm(bot, ends_on: int, alarm_set: bool):
    """
    Updates the alarm_set status of an auction reminder.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE auction_reminders SET alarm_set = $1 WHERE ends_on = $2",
                alarm_set,
                ends_on,
            )
        pretty_log(
            tag="db",
            message=f"Updated auction reminder for ends_on {ends_on} to alarm_set={alarm_set}.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update auction reminder for ends_on {ends_on}: {e}",
        )

async def delete_auction_reminder(bot, ends_on: int):
    """
    Deletes an auction reminder from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM auction_reminders WHERE ends_on = $1",
                ends_on,
            )
        pretty_log(
            tag="db",
            message=f"Deleted auction reminder for ends_on {ends_on}.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete auction reminder for ends_on {ends_on}: {e}",
        )

async def fetch_all_auction_reminders(bot):
    """
    Fetches all auction reminders from the database.
    Returns a list of dictionaries with keys 'ends_on' and 'alarm_set'.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT ends_on, alarm_set FROM auction_reminders")
            reminders = [{"ends_on": row["ends_on"], "alarm_set": row["alarm_set"]} for row in rows]
            return reminders
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch auction reminders: {e}",
        )
        return []

async def delete_all_auction_reminders(bot):
    """
    Deletes all auction reminders from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM auction_reminders")
        pretty_log(
            tag="db",
            message="Deleted all auction reminders.",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete all auction reminders: {e}",
        )