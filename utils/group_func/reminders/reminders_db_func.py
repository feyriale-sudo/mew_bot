# utils/database/user_reminders_db_functions.py
import asyncpg
import discord
# 🟣 Reminder ID Autocomplete
from discord import app_commands

from utils.logs.pretty_log import pretty_log

# 🔮────────────────────────────────────────────
#           ✨ Reminder DB Functions
# 🔮────────────────────────────────────────────



# 🟣 Reminder ID Autocomplete (User-specific)
async def reminder_id_autocomplete(interaction: discord.Interaction, current: str):
    """
    Autocomplete showing the global reminder_id:
      "Reminder ID 4: My reminder title"
    Filters by 'current' and returns up to 25 choices.
    """
    reminders = await fetch_all_user_reminders(interaction.client, interaction.user.id)

    choices = []
    q = (current or "").lower().strip()

    for r in reminders:
        # prefer title, fall back to message
        title = r.get("title") or r.get("message") or ""
        if not title:
            continue

        # filter by the user's typed text (if any)
        if q and q not in title.lower():
            continue

        # Use the global reminder_id in display and as the returned value
        display = f"Reminder ID {r['user_reminder_id']}: {title}"
        choices.append(
            app_commands.Choice(
                name=display[:100],
                value=str(r["user_reminder_id"])  # 🔑 convert to string
            )
        )


        if len(choices) >= 25:
            break

    return choices


async def upsert_user_reminder(
    bot,
    user_id: int,
    message: str,
    remind_on,
    user_name: str = None,
    ping_role_1: int = None,
    ping_role_2: int = None,
    repeat_interval: int = None,
    title: str = None,
    color: int = None,
    image_url: str = None,
    thumbnail_url: str = None,
    footer_text: str = None,
):
    """Insert a new reminder for a user, assigning user_reminder_id automatically."""
    async with bot.pg_pool.acquire() as conn:
        # Get next user_reminder_id for this user
        row = await conn.fetchrow(
            "SELECT COALESCE(MAX(user_reminder_id), 0) + 1 AS next_id FROM user_reminders WHERE user_id = $1;",
            user_id,
        )
        user_reminder_id = row["next_id"]


        await conn.execute(
            """
            INSERT INTO user_reminders
            (user_id, user_reminder_id, user_name, message, ping_role_1, ping_role_2,
             remind_on, repeat_interval, title, color, image_url, thumbnail_url, footer_text)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13);
            """,
            user_id,
            user_reminder_id,
            user_name,
            message,
            ping_role_1,
            ping_role_2,
            remind_on,
            repeat_interval,
            title,
            color,
            image_url,
            thumbnail_url,
            footer_text,
        )

# 🟣 Update Reminder by User Reminder ID
async def update_user_reminder(
    bot,
    user_id: int,
    user_reminder_id: int,
    fields: dict,
):
    """
    Update one or more fields for a user's reminder using user_reminder_id.

    Example:
        await update_user_reminder(bot, 12345, 1, {
            "message": "New message",
            "remind_on": new_timestamp,
            "color": 0xFF00FF
        })
    """
    if not fields:
        pretty_log(
            tag="warn",
            message=f"[Reminder Update] Skipped update: No fields provided for user_id={user_id}, reminder_id={user_reminder_id}",
        )
        return  # Nothing to update

    async with bot.pg_pool.acquire() as conn:
        try:
            # Dynamically build the SET clause with numbered placeholders
            set_clauses = []
            values = []
            for i, (key, value) in enumerate(fields.items(), start=1):
                set_clauses.append(f"{key} = ${i}")
                values.append(value)

            # Append the identifying fields as the last parameters
            values.append(user_id)
            values.append(user_reminder_id)

            query = f"""
            UPDATE user_reminders
            SET {', '.join(set_clauses)}
            WHERE user_id = ${len(values)-1} AND user_reminder_id = ${len(values)};
            """

            pretty_log(
                tag="db",
                message=f"[Reminder Update] Attempting update for user_id={user_id}, reminder_id={user_reminder_id}, fields={fields}",
            )

            result = await conn.execute(query, *values)

            if result == "UPDATE 0":
                pretty_log(
                    tag="warn",
                    message=f"[Reminder Update] No rows matched for user_id={user_id}, reminder_id={user_reminder_id}",
                )
            else:
                pretty_log(
                    tag="success",
                    message=f"[Reminder Update] Success: {result} for user_id={user_id}, reminder_id={user_reminder_id}",
                )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"[Reminder Update] Failed for user_id={user_id}, reminder_id={user_reminder_id}, fields={fields}: {e}",
                include_trace=True,
            )
            raise


# 🟣 Update by Field
async def update_reminder_field(bot, reminder_id: int, field: str, value):
    """Update a single field for a given reminder_id."""
    async with bot.pg_pool.acquire() as conn:
        query = f"UPDATE user_reminders SET {field} = $1 WHERE reminder_id = $2;"
        await conn.execute(query, value, reminder_id)


# 🟣 Update multiple fields for a reminder
async def update_reminder_fields(bot, reminder_id: int, fields: dict):
    """
    Update multiple fields for a given reminder_id.

    Example:
        await update_reminder_fields(bot, 123, {
            "message": "New message",
            "remind_on": new_timestamp,
            "color": 0xFF00FF
        })
    """
    if not fields:
        return  # nothing to update

    async with bot.pg_pool.acquire() as conn:
        # Dynamically build the SET part with numbered placeholders
        set_clauses = []
        values = []
        for i, (key, value) in enumerate(fields.items(), start=1):
            set_clauses.append(f"{key} = ${i}")
            values.append(value)

        # Append the reminder_id as the last parameter
        values.append(reminder_id)
        query = f"UPDATE user_reminders SET {', '.join(set_clauses)} WHERE reminder_id = ${len(values)};"

        await conn.execute(query, *values)


# 🟣 Remove One
async def remove_reminder(bot, reminder_id: int):
    """Remove a reminder by reminder_id."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM user_reminders WHERE reminder_id = $1;", reminder_id
        )


# 🟣 Fetch One
async def fetch_reminder(bot, reminder_id: int):
    """Fetch a single reminder by reminder_id."""
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM user_reminders WHERE reminder_id = $1;", reminder_id
        )


# 🟣 Fetch One Reminder by User
async def fetch_user_reminder(bot, user_id: int, reminder_id: int):
    """
    Fetch a single reminder by reminder_id, but only if it belongs to the given user_id.
    Returns None if not found or doesn't belong to the user.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM user_reminders
            WHERE user_reminder_id = $1 AND user_id = $2;
            """,
            reminder_id,
            user_id,
        )


# 🟣 Remove All by User
async def remove_all_user_reminders(bot, user_id: int):
    """Delete all reminders for a given user."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute("DELETE FROM user_reminders WHERE user_id = $1;", user_id)


# 🟣 Remove One Reminder by User-Scoped ID
async def remove_user_reminder(bot, user_id: int, user_reminder_id: int):
    """
    Remove a single reminder for a specific user using the per-user incremental ID.
    Returns True if a row was deleted, False otherwise.
    """
    async with bot.pg_pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM user_reminders
            WHERE user_id = $1 AND user_reminder_id = $2;
            """,
            user_id,
            user_reminder_id,
        )
        # asyncpg execute returns a string like "DELETE 1" if a row was deleted
        return result.split()[-1] != "0"


# 🟣 Fetch All
async def fetch_all_reminders(bot):
    """Fetch all reminders in the table."""
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM user_reminders;")


# 🟣 Fetch All Reminders for a User
async def fetch_all_user_reminders(bot, user_id: int):
    """Fetch all reminders for a specific user."""
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM user_reminders WHERE user_id = $1 ORDER BY remind_on ASC;",
            user_id,
        )


# 🟣 Fetch Due
async def fetch_due_reminders(bot):
    """Fetch reminders that are due now or earlier (using UNIX seconds)."""
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM user_reminders
            WHERE remind_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
            ORDER BY remind_on ASC;
            """
        )
