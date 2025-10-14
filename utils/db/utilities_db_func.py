# 🟣────────────────────────────────────────────
#        Utilities DB Functions for Mew (bot.pg_pool)
# 🟣────────────────────────────────────────────

import discord
from utils.logs.pretty_log import pretty_log


# --------------------
#  Upsert a user utility setting (now supports faction_ball_alert)
# --------------------
async def set_user_utility(
    bot,
    user_id: int,
    user_name: str | None = None,
    fish_rarity: str | None = None,
    faction_ball_alert: str | None = None,
):
    """
    Insert or update a user's utility settings.
    Only fields provided (not None) will be updated.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO utilities (user_id, user_name, fish_rarity, faction_ball_alert)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    user_name = COALESCE($2, utilities.user_name),
                    fish_rarity = COALESCE($3, utilities.fish_rarity),
                    faction_ball_alert = COALESCE($4, utilities.faction_ball_alert)
                """,
                user_id,
                user_name,
                fish_rarity,
                faction_ball_alert,
            )

        pretty_log(
            tag="db",
            message=f"Set utility settings for user {user_id} ({user_name})",
            bot=bot,
        )

        # Update cache
        from utils.cache.utility_cache import set_user_utility_cached

        set_user_utility_cached(
            user_id,
            user_name=user_name,
            fish_rarity=fish_rarity,
            faction_ball_alert=faction_ball_alert,
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set utility settings for user {user_id}: {e}",
            bot=bot,
        )


# --------------------
#  Fetch all utilities
# --------------------
async def fetch_all_utilities(bot) -> list[dict]:
    """
    Return all rows in utilities table as list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM utilities")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch utilities: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Fetch single user by ID (now includes faction_ball_alert)
# --------------------
async def fetch_user_utility(bot, user_id: int) -> dict | None:
    """
    Return a single user's utility data.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM utilities WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch utility for user {user_id}: {e}",
            bot=bot,
        )
        return None

# --------------------
#  Update faction_ball_alert
# --------------------
async def update_faction_ball_alert(
    bot, user: discord.Member, faction_ball_alert: str
) -> bool:
    """
    Update a user's faction_ball_alert setting.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE utilities SET faction_ball_alert = $1 WHERE user_id = $2",
                faction_ball_alert,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated faction_ball_alert for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.utility_cache import update_faction_ball_alert_in_cache

        update_faction_ball_alert_in_cache(user, faction_ball_alert)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update faction_ball_alert for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Fetch users by fish rarity
# --------------------
async def fetch_users_by_fish_rarity(bot, fish_rarity: str) -> list[dict]:
    """
    Return all users with a specific fish rarity.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM utilities WHERE fish_rarity = $1", fish_rarity
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch users by fish rarity {fish_rarity}: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Update fish rarity
# --------------------
async def update_fish_rarity(bot, user: discord.Member, fish_rarity: str) -> bool:
    """
    Update a user's fish rarity setting.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE utilities SET fish_rarity = $1 WHERE user_id = $2",
                fish_rarity,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated fish rarity for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.utility_cache import update_fish_rarity_in_cache

        update_fish_rarity_in_cache(user, fish_rarity)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update fish rarity for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Delete user utility
# --------------------
async def delete_user_utility(bot, user: discord.Member) -> bool:
    """
    Delete a user's utility data.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM utilities WHERE user_id = $1", user_id
            )
        deleted = result.endswith("DELETE 1")
        pretty_log(
            tag="db",
            message=f"Deleted utility data for {user_name}: {deleted}",
            bot=bot,
        )
        # Remove from cache
        from utils.cache.utility_cache import delete_user_utility_from_cache

        delete_user_utility_from_cache(user)
        return deleted
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete utility data for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Check if user exists
# --------------------
async def user_utility_exists(bot, user_id: int) -> bool:
    """
    Check if a user exists in the utilities table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM utilities WHERE user_id = $1", user_id
            )
            return row is not None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to check if user {user_id} exists: {e}",
            bot=bot,
        )
        return False
