# 🟣────────────────────────────────────────────
#        Timers DB Functions for Mew (bot.pg_pool)
# 🟣────────────────────────────────────────────

from utils.logs.pretty_log import pretty_log


# --------------------
#  Upsert a timer setting field for a user
# --------------------
async def set_timer(
    bot,
    user_id: int,
    user_name: str | None = None,
    pokemon_setting: str | None = None,
    fish_setting: str | None = None,
    battle_setting: str | None = None,
    catchbot_setting: str | None = None,
    quest_setting: str | None = None,
):
    """
    Insert or update a user's timer settings.
    Only fields provided (not None) will be updated.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO timers (user_id, user_name, pokemon_setting, fish_setting, battle_setting, catchbot_setting, quest_setting)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE SET
                    user_name = COALESCE($2, timers.user_name),
                    pokemon_setting = COALESCE($3, timers.pokemon_setting),
                    fish_setting = COALESCE($4, timers.fish_setting),
                    battle_setting = COALESCE($5, timers.battle_setting),
                    catchbot_setting = COALESCE($6, timers.catchbot_setting),
                    quest_setting = COALESCE($7, timers.quest_setting)
                """,
                user_id,
                user_name,
                pokemon_setting,
                fish_setting,
                battle_setting,
                catchbot_setting,
                quest_setting,
            )

        pretty_log(
            tag="db",
            message=f"Set timer settings for user {user_id} ({user_name})",
            bot=bot,
        )
        from utils.cache.timers_cache import set_timer_cached
        # Update cache as well
        set_timer_cached(
            user_id,
            user_name,
            pokemon_setting,
            fish_setting,
            battle_setting,
            catchbot_setting,
            quest_setting,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set timer settings for user {user_id}: {e}",
            bot=bot,
        )


# --------------------
#  Fetch all rows
# --------------------
async def fetch_all_timers(bot) -> list[dict]:
    """
    Return all rows in timers table as list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM timers")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch timers: {e}",
            bot=bot,
        )
        return []


# --------------------
#  Fetch single user by ID
# --------------------
async def fetch_timer(bot, user_id: int) -> dict | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM timers WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch timer for user {user_id}: {e}",
            bot=bot,
        )
        return None


# --------------------
#  Delete user timers
# --------------------
async def delete_timer(bot, user_id: int) -> bool:
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM timers WHERE user_id = $1", user_id
            )
        deleted = result.endswith("DELETE 1")
        pretty_log(
            tag="db",
            message=f"Deleted timers for user {user_id}: {deleted}",
            bot=bot,
        )
        return deleted
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete timers for user {user_id}: {e}",
            bot=bot,
        )
        return False
