# SQL SCRIPT
"""
DROP TABLE IF EXISTS auction_reminders;
CREATE TABLE auction_reminders (
    ends_on BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    user_name TEXT NOT NULL,
    alarm_set BOOLEAN,
    PRIMARY KEY (ends_on, user_id)
);
"""
import discord

from utils.logs.pretty_log import pretty_log


async def is_timestamp_more_than_5_hours_away(
    bot, timestamp: int, user_id: int
) -> bool:
    """
    Returns True if the given timestamp is more than 5 hours away from all ends_on values in the DB for the given user_id.
    Accepts bot as the first argument to use bot.pg_pool for DB connection.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            query = "SELECT ends_on FROM auction_reminders WHERE user_id = $1"
            rows = await conn.fetch(query, user_id)
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


async def upsert_auction_reminder(
    bot, ends_on: int, user_id: int, user_name: str, alarm_set: bool
):
    """
    Inserts or updates an auction reminder in the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO auction_reminders (ends_on, user_id, user_name, alarm_set)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (ends_on, user_id) DO UPDATE SET user_name = $3, alarm_set = $4
                """,
                ends_on,
                user_id,
                user_name,
                alarm_set,
            )
        pretty_log(
            tag="db",
            message=f"Upserted auction reminder for ends_on {ends_on}, user_id {user_id}, user_name {user_name} with alarm_set={alarm_set}.",
        )
        # Upsert into cache as well
        from utils.cache.auction_reminder_cache import upsert_auction_reminder_cache

        upsert_auction_reminder_cache(ends_on, user_id, user_name, alarm_set)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert auction reminder for ends_on {ends_on}, user_id {user_id}: {e}",
        )


async def fetch_auction_reminder(bot, ends_on: int, user_id: int):
    """
    Fetches an auction reminder by ends_on and user_id from the database.
    Returns a dictionary with keys 'ends_on', 'user_id', 'user_name', and 'alarm_set', or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT ends_on, user_id, user_name, alarm_set FROM auction_reminders WHERE ends_on = $1 AND user_id = $2",
                ends_on,
                user_id,
            )
            if row:
                return {
                    "ends_on": row["ends_on"],
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "alarm_set": row["alarm_set"],
                }
            else:
                return None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch auction reminder for ends_on {ends_on}, user_id {user_id}: {e}",
        )
        return None


async def update_auction_reminder_alarm(
    bot, ends_on: int, user_id: int, alarm_set: bool
):
    """
    Updates the alarm_set status of an auction reminder for a specific user.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE auction_reminders SET alarm_set = $1 WHERE ends_on = $2 AND user_id = $3",
                alarm_set,
                ends_on,
                user_id,
            )
        pretty_log(
            tag="db",
            message=f"Updated auction reminder for ends_on {ends_on}, user_id {user_id} to alarm_set={alarm_set}.",
        )
        # Update cache as well
        from utils.cache.auction_reminder_cache import update_auction_reminder_cache

        update_auction_reminder_cache(ends_on, user_id, alarm_set)

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update auction reminder for ends_on {ends_on}, user_id {user_id}: {e}",
        )


async def delete_auction_reminder(bot, ends_on: int, user_id: int):
    """
    Deletes an auction reminder for a specific user from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM auction_reminders WHERE ends_on = $1 AND user_id = $2",
                ends_on,
                user_id,
            )
        pretty_log(
            tag="db",
            message=f"Deleted auction reminder for ends_on {ends_on}, user_id {user_id}.",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete auction reminder for ends_on {ends_on}, user_id {user_id}: {e}",
        )


async def fetch_all_auction_reminders(bot):
    """
    Fetches all auction reminders from the database.
    Returns a list of dictionaries with keys 'ends_on', 'user_id', 'user_name', and 'alarm_set'.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT ends_on, user_id, user_name, alarm_set FROM auction_reminders"
            )
            reminders = [
                {
                    "ends_on": row["ends_on"],
                    "user_id": row["user_id"],
                    "user_name": row["user_name"],
                    "alarm_set": row["alarm_set"],
                }
                for row in rows
            ]
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
        # Also clear the cache
        from utils.cache.auction_reminder_cache import (
            remove_all_auction_reminders_cache,
        )

        remove_all_auction_reminders_cache()
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete all auction reminders: {e}",
        )
