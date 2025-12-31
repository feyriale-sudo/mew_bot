import time

from utils.logs.pretty_log import pretty_log

# SQL SCRIPT
"""CREATE TABLE battletower (
    user_id TEXT PRIMARY KEY,
    user_name TEXT NOT NULL,
    registered_at BIGINT NOT NULL
);"""


# 🍥──────────────────────────────────────────────
#   Register a User for Battle Tower
# 🍥──────────────────────────────────────────────
async def register_battletower_user(bot, user_id: int, user_name: str):
    """Register a user for the Battle Tower."""

    registered_at = int(time.time())
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO battletower (user_id, user_name, registered_at) "
                "VALUES ($1, $2, $3) "
                "ON CONFLICT (user_id) DO NOTHING",
                user_id,
                user_name,
                registered_at,
            )
        pretty_log(
            tag="db",
            message=f"Registered user {user_name} ({user_id}) for Battle Tower.",
            bot=bot,
        )
        # Also update the cache
        from utils.cache.battle_tower_cache import upsert_battle_tower_cache

        upsert_battle_tower_cache(user_id, user_name, registered_at)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to register Battle Tower user {user_name} ({user_id}): {e}",
            bot=bot,
        )


# 🍭──────────────────────────────────────────────
#   Remove a User from Battle Tower
# 🍭──────────────────────────────────────────────
async def remove_battletower_user(bot, user_id: int):
    """Remove a user from the Battle Tower."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM battletower WHERE user_id = $1",
                user_id,
            )
        pretty_log(
            tag="db",
            message=f"Removed user ({user_id}) from Battle Tower.",
            bot=bot,
        )
        # Also remove from the cache
        from utils.cache.battle_tower_cache import remove_battle_tower_cache

        remove_battle_tower_cache(user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to remove Battle Tower user ({user_id}): {e}",
            bot=bot,
        )


# 🍡──────────────────────────────────────────────
#   Fetch All Registered Battle Tower Users
# 🍡──────────────────────────────────────────────
async def fetch_battletower_users(bot):
    """Fetch all registered Battle Tower users."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM battletower")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch Battle Tower users: {e}",
            bot=bot,
        )
        return []


# 🍢──────────────────────────────────────────────
#   Check if a User is Registered for Battle Tower
# 🍢──────────────────────────────────────────────
async def is_battletower_user_registered(bot, user_id: int) -> bool:
    """Check if a user is registered for the Battle Tower."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM battletower WHERE user_id = $1",
                user_id,
            )
            return row is not None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to check Battle Tower registration for user ({user_id}): {e}",
            bot=bot,
        )
        return False


# 🍣──────────────────────────────────────────────
#   Clear All Battle Tower Registrations
# 🍣──────────────────────────────────────────────
async def clear_battletower_registrations(bot):
    """Clear all Battle Tower registrations."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM battletower")
        pretty_log(
            tag="db",
            message="Cleared all Battle Tower registrations.",
            bot=bot,
        )
        # Also clear the cache
        from utils.cache.cache_list import battle_tower_cache

        battle_tower_cache.clear()
        pretty_log(
            tag="cache",
            message="Cleared Battle Tower cache.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to clear Battle Tower registrations: {e}",
            bot=bot,
        )
