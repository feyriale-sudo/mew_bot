import discord

from utils.logs.pretty_log import pretty_log


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Spooky Hour DB Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def upsert_spooky_hour(bot: discord.Client, ends_on: int, message_id: int = None):
    """
    Upserts the spooky_hour row with the given ends_on and optional message_id value.
    """
    query = """
        INSERT INTO spooky_hour (id, ends_on, message_id)
        VALUES (1, $1, $2)
        ON CONFLICT (id) DO UPDATE SET ends_on = EXCLUDED.ends_on, message_id = EXCLUDED.message_id
    """
    params = (ends_on, message_id)
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, *params)
        pretty_log(
            "success",
            f"Upserted spooky_hour with ends_on {ends_on}"
            + (f" and message_id {message_id}" if message_id else ""),
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert spooky_hour: {e}",
        )


async def remove_spooky_hour(bot: discord.Client):
    """
    Removes the row from spooky_hour table.
    """
    query = "DELETE FROM spooky_hour"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query)
        pretty_log(
            "success",
            "Removed spooky_hour row",
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove spooky_hour row: {e}",
        )


async def fetch_spooky_hour(bot: discord.Client):
    """
    Fetches the spooky_hour row.
    Returns a dict with ends_on and message_id, or None if not found.
    """
    query = "SELECT ends_on, message_id FROM spooky_hour LIMIT 1"
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query)
        if row:
            return {"ends_on": row["ends_on"], "message_id": row["message_id"]}
        return None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch spooky_hour row: {e}",
        )
        return None
