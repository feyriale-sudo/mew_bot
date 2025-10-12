from utils.logs.pretty_log import pretty_log
from utils.db.timers_db_func import fetch_all_timers, fetch_timer
from utils.cache.cache_list import timer_cache


# 🟣────────────────────────────────────────────
#        Timer Cache Loader
# ─────────────────────────────────────────────
async def load_timer_cache(bot):
    """
    Load all user timer settings into memory cache.
    Uses the fetch_all_timers DB function.
    """
    timer_cache.clear()

    rows = await fetch_all_timers(bot)
    for row in rows:
        timer_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "pokemon_setting": row.get("pokemon_setting"),
            "fish_setting": row.get("fish_setting"),
            "battle_setting": row.get("battle_setting"),
            "catchbot_setting": row.get("catchbot_setting"),
            "quest_setting": row.get("quest_setting"),
        }

    # 🐭 Debug log
    pretty_log(
        tag="",
        message=f"Loaded {len(timer_cache)} users' timer settings into cache",
        label="⌚ TIMER CACHE",
        bot=bot,
    )

    return timer_cache



# --------------------
#  Set or update user timer settings
# --------------------
def set_timer_cached(
    user_id: int,
    user_name: str | None = None,
    pokemon_setting: str | None = None,
    fish_setting: str | None = None,
    battle_setting: str | None = None,
    catchbot_setting: str | None = None,
    quest_setting: str | None = None,
):
    """
    Cached version of set_timer that updates cache.
    Only fields provided (not None) will be updated.
    """

    try:
        # 🔹 Update cache first
        if user_id not in timer_cache:
            timer_cache[user_id] = {
                "user_name": None,
                "pokemon_setting": "off",
                "fish_setting": "off",
                "battle_setting": "off",
                "catchbot_setting": "off",
                "quest_setting": "off",
            }

        # Update only provided fields in cache
        if user_name is not None:
            timer_cache[user_id]["user_name"] = user_name
        if pokemon_setting is not None:
            timer_cache[user_id]["pokemon_setting"] = pokemon_setting
        if fish_setting is not None:
            timer_cache[user_id]["fish_setting"] = fish_setting
        if battle_setting is not None:
            timer_cache[user_id]["battle_setting"] = battle_setting
        if catchbot_setting is not None:
            timer_cache[user_id]["catchbot_setting"] = catchbot_setting
        if quest_setting is not None:
            timer_cache[user_id]["quest_setting"] = quest_setting


        pretty_log(
            tag="cache",
            message=f"Updated timer cache for user {user_id} ({user_name})",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update timer cache for user {user_id}: {e}",
        )


async def fetch_timer_cached(bot, user_id: int) -> dict | None:
    """
    Cached version of fetch_timer that checks cache first, then database if not found.
    """
    try:
        # 🔹 Check cache first
        if user_id in timer_cache:
            return timer_cache[user_id].copy()

        # 🔹 Not in cache, fetch from database
        db_result = await fetch_timer(bot, user_id)
        if db_result:
            # Add to cache for future use
            timer_cache[user_id] = {
                "user_name": db_result.get("user_name"),
                "pokemon_setting": db_result.get("pokemon_setting", "off"),
                "fish_setting": db_result.get("fish_setting", "off"),
                "battle_setting": db_result.get("battle_setting", "off"),
                "catchbot_setting": db_result.get("catchbot_setting", "off"),
                "quest_setting": db_result.get("quest_setting", "off"),
            }
            return timer_cache[user_id].copy()

        return None

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch timer from cache for user {user_id}: {e}",
            bot=bot,
        )
        return None

