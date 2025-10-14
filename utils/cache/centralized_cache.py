# 💜────────────────────────────────────────────
#       🟣 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# 💜────────────────────────────────────────────

from utils.cache.cache_list import (
    daily_faction_ball_cache,
    market_alert_cache,
    market_value_cache,
    missing_pokemon_cache,
    schedule_cache,
    timer_cache,
    user_info_cache,
    utility_cache,
)
from utils.cache.daily_fa_ball_cache import load_daily_faction_ball_cache
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.cache.missing_pokemon_cache import load_missing_pokemon_cache
from utils.cache.schedule_cache import load_schedule_cache
from utils.cache.timers_cache import load_timer_cache
from utils.cache.user_info_cache import load_user_info_cache
from utils.cache.utility_cache import load_utility_cache
from utils.db.market_value_db_func import load_market_cache_from_db
from utils.logs.pretty_log import pretty_log


# 💜────────────────────────────────────────────
#     🟣 Load Everything in One Go
# 💜────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader and logs memory summary.
    """
    try:
        # 🌸 Load Market Alerts
        await load_market_alert_cache(bot)

        # 🌸 Load Missing Pokémon
        await load_missing_pokemon_cache(bot)

        # 🌸 Load Timer Settings
        await load_timer_cache(bot)

        # 🌸 Load Schedule Settings
        await load_schedule_cache(bot)

        # 🌸 Load Utility Settings
        await load_utility_cache(bot)

        # 🌸 Load User Info
        await load_user_info_cache(bot)

        # 🌸 Load Market Value Cache
        await load_market_cache_from_db(bot)

        # 🌸 Load Daily Faction Ball Cache
        await load_daily_faction_ball_cache(bot)

        # 🎀 Unified summary log
        pretty_log(
            tag="",
            label="🦋 CENTRAL CACHE",
            message=(
                f"All caches refreshed and loaded "
                f"(Market Alerts: {len(market_alert_cache)} ~{get_deep_size(market_alert_cache)//1024} KB + "
                f"Missing Pokémon: {len(missing_pokemon_cache)} ~{get_deep_size(missing_pokemon_cache)//1024} KB +"
                f"Timer Settings: {len(timer_cache)} ~{get_deep_size(timer_cache)//1024} KB) +"
                f"Schedule Settings: {len(schedule_cache)} ~{get_deep_size(schedule_cache)//1024} KB +"
                f"Utility Settings: {len(utility_cache)} ~{get_deep_size(utility_cache)//1024} KB + "
                f"User Info: {len(user_info_cache)} ~{get_deep_size(user_info_cache)//1024} KB + "
                f"Daily Faction Balls: {len(daily_faction_ball_cache)} ~{get_deep_size(daily_faction_ball_cache)//1024} KB + "
                f"Market Values: {len(market_value_cache)} ~{get_deep_size(market_value_cache)//1024} KB = "
                f"Total Approx: ~{(get_deep_size(market_alert_cache) + get_deep_size(missing_pokemon_cache) + get_deep_size(timer_cache) + get_deep_size(schedule_cache) + get_deep_size(utility_cache) + get_deep_size(user_info_cache) + get_deep_size(daily_faction_ball_cache) + get_deep_size(market_value_cache))//1024} KB"
            ),
        ),
    except Exception as e:
        pretty_log(
            tag="error",
            label="🦋 CENTRAL CACHE",
            message=f"Failed to load all caches: {e}",
        )


# 💜────────────────────────────────────────────
#       🟣 Memory Size Helper 💜
# 💜────────────────────────────────────────────
import sys


def get_deep_size(obj, seen=None):
    """
    Recursively calculate approximate memory size of an object in bytes.
    """
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(
            get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items()
        )
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_deep_size(i, seen) for i in obj)

    return size
