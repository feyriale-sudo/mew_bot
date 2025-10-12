from utils.logs.pretty_log import pretty_log
from utils.db.schedule_db_func import fetch_all_schedules, fetch_user_schedules
from utils.cache.cache_list import schedule_cache


# 🌸────────────────────────────────────────────
#        Schedule Cache Loader
# ─────────────────────────────────────────────
async def load_schedule_cache(bot):
    """
    Load all user schedule settings into memory cache.
    Uses the fetch_all_schedules DB function.
    """
    schedule_cache.clear()

    rows = await fetch_all_schedules(bot)
    for row in rows:
        user_id = row["user_id"]

        # Initialize user's schedule list if not exists
        if user_id not in schedule_cache:
            schedule_cache[user_id] = []

        # Add reminder to user's schedule list
        schedule_cache[user_id].append(
            {
                "reminder_id": row.get("reminder_id"),
                "user_id": row.get("user_id"),
                "user_name": row.get("user_name"),
                "type": row.get("type"),
                "scheduled_on": row.get("scheduled_on"),
            }
        )

    # 🌸 Debug log
    total_reminders = sum(len(reminders) for reminders in schedule_cache.values())
    pretty_log(
        tag="",
        message=f"Loaded {len(schedule_cache)} users with {total_reminders} total reminders into cache",
        label="📅 SCHEDULE CACHE",
        bot=bot,
    )

    return schedule_cache


# 🌸────────────────────────────────────────────
#  Set or update user schedule
# ────────────────────────────────────────────
def set_schedule_cached(
    user_id: int,
    reminder_id: int,
    user_name: str,
    type_: str,
    scheduled_on: int,
):
    """
    Add or update a reminder in the cache.
    """
    try:
        # Initialize user's schedule list if not exists
        if user_id not in schedule_cache:
            schedule_cache[user_id] = []

        # Check if reminder already exists (by type)
        existing_index = None
        for i, reminder in enumerate(schedule_cache[user_id]):
            if reminder["type"] == type_:
                existing_index = i
                break

        new_reminder = {
            "reminder_id": reminder_id,
            "user_id": user_id,
            "user_name": user_name,
            "type": type_,
            "scheduled_on": scheduled_on,
        }

        if existing_index is not None:
            # Update existing reminder
            schedule_cache[user_id][existing_index] = new_reminder
        else:
            # Add new reminder
            schedule_cache[user_id].append(new_reminder)

        pretty_log(
            tag="cache",
            message=f"Updated schedule cache for user {user_id} ({user_name}) - {type_}",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update schedule cache for user {user_id}: {e}",
        )


# 🌸────────────────────────────────────────────
#  Fetch user schedules from cache
# ────────────────────────────────────────────
async def fetch_user_schedules_cached(bot, user_id: int) -> list[dict]:
    """
    Cached version of fetch_user_schedules that checks cache first, then database if not found.
    """
    try:
        # Check cache first
        if user_id in schedule_cache:
            return schedule_cache[user_id].copy()

        # Not in cache, fetch from database
        db_results = await fetch_user_schedules(bot, user_id)
        if db_results:
            # Add to cache for future use
            schedule_cache[user_id] = []
            for reminder in db_results:
                schedule_cache[user_id].append(
                    {
                        "reminder_id": reminder.get("reminder_id"),
                        "user_id": reminder.get("user_id"),
                        "user_name": reminder.get("user_name"),
                        "type": reminder.get("type"),
                        "scheduled_on": reminder.get("scheduled_on"),
                    }
                )
            return schedule_cache[user_id].copy()

        return []

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch schedules from cache for user {user_id}: {e}",
            bot=bot,
        )
        return []


# 🌸────────────────────────────────────────────
#  Remove schedule from cache
# ────────────────────────────────────────────
def remove_schedule_cached(user_id: int, type_: str):
    """
    Remove a specific reminder type from user's cache.
    """
    try:
        if user_id not in schedule_cache:
            return

        # Filter out the specific type
        schedule_cache[user_id] = [
            reminder
            for reminder in schedule_cache[user_id]
            if reminder["type"] != type_
        ]

        # Remove user entirely if no reminders left
        if not schedule_cache[user_id]:
            del schedule_cache[user_id]

        pretty_log(
            tag="cache",
            message=f"Removed {type_} schedule from cache for user {user_id}",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to remove schedule from cache for user {user_id}: {e}",
        )


# 🌸────────────────────────────────────────────
#  Get due reminders from cache
# ────────────────────────────────────────────
def get_due_reminders_cached(current_timestamp: int) -> list[dict]:
    """
    Get all reminders that are due from cache (scheduled_on <= current_timestamp).
    Returns a flat list of reminder dictionaries.
    """
    try:
        due_reminders = []

        for user_id, reminders in schedule_cache.items():
            for reminder in reminders:
                if reminder["scheduled_on"] <= current_timestamp:
                    due_reminders.append(reminder.copy())

        # Sort by scheduled_on (earliest first)
        due_reminders.sort(key=lambda x: x["scheduled_on"])

        return due_reminders

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to get due reminders from cache: {e}",
        )
        return []


# 🌸────────────────────────────────────────────
#  Remove reminder by ID from cache
# ────────────────────────────────────────────
def remove_reminder_by_id_cached(reminder_id: int):
    """
    Remove a specific reminder by its ID from cache.
    """
    try:
        for user_id, reminders in schedule_cache.items():
            for i, reminder in enumerate(reminders):
                if reminder["reminder_id"] == reminder_id:
                    # Remove the reminder
                    del schedule_cache[user_id][i]

                    # Remove user entirely if no reminders left
                    if not schedule_cache[user_id]:
                        del schedule_cache[user_id]

                    pretty_log(
                        tag="cache",
                        message=f"Removed reminder {reminder_id} from cache",
                    )
                    return True

        return False

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to remove reminder {reminder_id} from cache: {e}",
        )
        return False
