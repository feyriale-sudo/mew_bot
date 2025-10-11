from typing import List, Optional
from datetime import datetime, timedelta
from utils.logs.pretty_log import pretty_log


# ────────────────────────────────────────────
#     🐱 Pokemeow Reminders Schedule DB 🐱
# ────────────────────────────────────────────
async def fetch_all_schedules(bot) -> list[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reminder_id, user_id, user_name, type, scheduled_on
                FROM pokemeow_reminders_schedule
                """
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(tag="error", message=f"Failed to fetch all schedules: {e}", bot=bot)
        return []


async def fetch_user_schedule(bot, user_id: int, type_: str) -> Optional[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT reminder_id, user_id, user_name, type, scheduled_on
                FROM pokemeow_reminders_schedule
                WHERE user_id=$1 AND type=$2
                """,
                user_id,
                type_,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch schedule for user {user_id}, type {type_}: {e}",
            bot=bot,
        )
        return None


# ────────────────────────────────────────────
#   🐱 Fetch User Schedule Rows
# ────────────────────────────────────────────
async def fetch_user_schedules(bot, user_id: int) -> List[dict]:
    """
    Fetch all reminder rows for a given user_id.
    Returns a list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reminder_id, user_id, user_name, type, scheduled_on
                FROM pokemeow_reminders_schedule
                WHERE user_id = $1
                """,
                user_id,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch schedules for user {user_id}: {e}",
            bot=bot,
        )
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Check if schedule exists with same timestamp & type
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def schedule_exists_with_same_ts(
    bot,
    user_id: int,
    type_: str,
    timestamp: int,
) -> bool:
    """
    Check if a row already exists for the given user_id, type, and timestamp.
    Returns True if found, False otherwise.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1
                FROM pokemeow_reminders_schedule
                WHERE user_id = $1
                  AND type = $2
                  AND scheduled_on = $3
                LIMIT 1
                """,
                user_id,
                type_,
                timestamp,
            )
            if row:
                pretty_log(
                    tag="debug",
                    message=f"[CB CHECK] Found existing schedule for {user_id} type={type_} ts={timestamp}",
                    bot=bot,
                )
                return True
            else:
                pretty_log(
                    tag="debug",
                    message=f"[CB CHECK] No existing schedule for {user_id} type={type_} ts={timestamp}",
                    bot=bot,
                )
                return False
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"[CB CHECK] Failed for {user_id}, type {type_}, ts={timestamp}: {e}",
            bot=bot,
        )
        return False


# ────────────────────────────────────────────
#   🐱 Upsert User Schedule Row
# ────────────────────────────────────────────
async def upsert_user_schedule(
    bot,
    user_id: int,
    user_name: str,
    type_: str,
    scheduled_on: int,
):
    """
    Insert or update a user's reminder schedule.
    Simplified to only store when the reminder should trigger.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pokemeow_reminders_schedule (user_id, user_name, type, scheduled_on)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, type) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    scheduled_on = EXCLUDED.scheduled_on,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id,
                user_name,
                type_,
                scheduled_on,
            )
        pretty_log(
            tag="db",
            message=f"Upserted schedule for user {user_name}, type {type_}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert schedule for user {user_name}, type {type_}: {e}",
            bot=bot,
        )

# ────────────────────────────────────────────
#   🐱 Delete User Schedule Row by Type
# ────────────────────────────────────────────
async def delete_user_schedule(bot, user_id: int, type_: str):
    """
    Delete a user's schedule row by type.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM pokemeow_reminders_schedule WHERE user_id=$1 AND type=$2",
                user_id,
                type_,
            )
        pretty_log(
            tag="db",
            message=f"Deleted schedule for user {user_id}, type {type_}",
            bot=bot,
        )
        return result.endswith("DELETE 1")
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete schedule for user {user_id}, type {type_}: {e}",
            bot=bot,
        )
        return False


# 🗑️ Delete reminder by ID
async def delete_reminder(bot, reminder_id: int):
    """
    Delete a specific reminder by its ID.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM pokemeow_reminders_schedule WHERE reminder_id = $1",
                reminder_id,
            )
        pretty_log(tag="db", message=f"Deleted reminder {reminder_id}", bot=bot)
        return result.endswith("DELETE 1")
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete reminder {reminder_id}: {e}",
            bot=bot,
        )
        return False


# ────────────────────────────────────────────
#   🐱 Fetch Reminders Due for Processing
# ────────────────────────────────────────────
async def fetch_due_reminders(bot, current_timestamp: int) -> List[dict]:
    """
    Fetch all reminders that are due (scheduled_on <= current_timestamp).
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reminder_id, user_id, user_name, type, scheduled_on
                FROM pokemeow_reminders_schedule
                WHERE scheduled_on <= $1
                ORDER BY scheduled_on ASC
                """,
                current_timestamp,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch due reminders: {e}",
            bot=bot,
        )
        return []
