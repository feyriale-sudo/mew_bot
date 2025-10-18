# 🟣────────────────────────────────────────────
#        User Info DB Functions for Mew (bot.pg_pool)
# 🟣────────────────────────────────────────────

import discord
from utils.logs.pretty_log import pretty_log


# --------------------
#  Upsert user info (now supports max_quests and current_quest_num)
# --------------------
async def set_user_info(
    bot,
    user_id: int,
    user_name: str | None = None,
    faction: str | None = None,
    patreon_tier: str | None = None,
    max_quests: int | None = None,
    current_quest_num: int | None = None,
):
    """
    Insert or update a user's info.
    Only fields provided (not None) will be updated.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_info (user_id, user_name, faction, patreon_tier, max_quests, current_quest_num)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE SET
                    user_name = COALESCE($2, user_info.user_name),
                    faction = COALESCE($3, user_info.faction),
                    patreon_tier = COALESCE($4, user_info.patreon_tier),
                    max_quests = COALESCE($5, user_info.max_quests),
                    current_quest_num = COALESCE($6, user_info.current_quest_num)
                """,
                user_id,
                user_name,
                faction,
                patreon_tier,
                max_quests,
                current_quest_num,
            )

        pretty_log(
            tag="db",
            message=f"Set user info for user {user_id} ({user_name})",
            bot=bot,
        )

        # Update cache
        from utils.cache.user_info_cache import set_user_info_cached

        set_user_info_cached(
            user_id,
            user_name=user_name,
            faction=faction,
            patreon_tier=patreon_tier,
            max_quests=max_quests,
            current_quest_num=current_quest_num,
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set user info for user {user_id}: {e}",
            bot=bot,
        )


# --------------------
#  Fetch all user info
# --------------------
async def fetch_all_user_info(bot) -> list[dict]:
    """
    Return all rows in user_info table as list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM user_info")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch user info: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Fetch single user by ID
# --------------------
async def fetch_user_info(bot, user_id: int) -> dict | None:
    """
    Return a single user's info data.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_info WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch user info for user {user_id}: {e}",
            bot=bot,
        )
        return None
# --------------------
#  Update max_quests
# --------------------
async def update_max_quests(bot, user: discord.Member, max_quests: int) -> bool:
    """
    Update a user's max_quests.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE user_info SET max_quests = $1 WHERE user_id = $2",
                max_quests,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated max_quests for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.user_info_cache import update_max_quests_in_cache

        update_max_quests_in_cache(user, max_quests)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update max_quests for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Update current_quest_num
# --------------------
async def update_current_quest_num(
    bot, user: discord.Member, current_quest_num: int
) -> bool:
    """
    Update a user's current_quest_num.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE user_info SET current_quest_num = $1 WHERE user_id = $2",
                current_quest_num,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated current_quest_num for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.user_info_cache import update_current_quest_num_in_cache

        update_current_quest_num_in_cache(user, current_quest_num)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update current_quest_num for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Fetch users by faction
# --------------------
async def fetch_users_by_faction(bot, faction: str) -> list[dict]:
    """
    Return all users with a specific faction.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM user_info WHERE faction = $1", faction
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch users by faction {faction}: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Fetch users by patreon tier
# --------------------
async def fetch_users_by_patreon_tier(bot, patreon_tier: str) -> list[dict]:
    """
    Return all users with a specific patreon tier.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM user_info WHERE patreon_tier = $1", patreon_tier
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch users by patreon tier {patreon_tier}: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Update faction
# --------------------
async def update_faction(bot, user: discord.Member, faction: str) -> bool:
    """
    Update a user's faction.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE user_info SET faction = $1 WHERE user_id = $2",
                faction,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated faction for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.user_info_cache import update_faction_in_cache

        update_faction_in_cache(user, faction)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update faction for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Update patreon tier
# --------------------
async def update_patreon_tier(bot, user: discord.Member, patreon_tier: str) -> bool:
    """
    Update a user's patreon tier.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE user_info SET patreon_tier = $1 WHERE user_id = $2",
                patreon_tier,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated patreon tier for {user_name}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.user_info_cache import update_patreon_tier_in_cache

        update_patreon_tier_in_cache(user, patreon_tier)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update patreon tier for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Update user name
# --------------------
async def update_user_name(bot, user: discord.Member, user_name: str) -> bool:
    """
    Update a user's name.
    """
    user_id = user.id
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE user_info SET user_name = $1 WHERE user_id = $2",
                user_name,
                user_id,
            )
        updated = result.endswith("UPDATE 1")
        pretty_log(
            tag="db",
            message=f"Updated user name for {user_id}: {updated}",
            bot=bot,
        )
        # Update cache
        from utils.cache.user_info_cache import update_user_name_in_cache

        update_user_name_in_cache(user, user_name)
        return updated
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update user name for {user_id}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Delete user info
# --------------------
async def delete_user_info(bot, user: discord.Member) -> bool:
    """
    Delete a user's info data.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_info WHERE user_id = $1", user_id
            )
        deleted = result.endswith("DELETE 1")
        pretty_log(
            tag="db",
            message=f"Deleted user info for {user_name}: {deleted}",
            bot=bot,
        )
        # Remove from cache
        from utils.cache.user_info_cache import delete_user_info_from_cache

        delete_user_info_from_cache(user)
        return deleted
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete user info for {user_name}: {e}",
            bot=bot,
        )
        return False


# --------------------
#  Check if user exists
# --------------------
async def user_info_exists(bot, user_id: int) -> bool:
    """
    Check if a user exists in the user_info table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM user_info WHERE user_id = $1", user_id
            )
            return row is not None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to check if user {user_id} exists: {e}",
            bot=bot,
        )
        return False
