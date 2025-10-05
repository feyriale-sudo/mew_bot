# 💜────────────────────────────────────────────
#       🟣 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# 💜────────────────────────────────────────────

from utils.cache.market_alert_cache import load_market_alert_cache
from utils.cache.cache_list import market_alert_cache, missing_pokemon_cache
from utils.logs.pretty_log import pretty_log
from utils.cache.missing_pokemon_cache import load_missing_pokemon_cache
# 💜────────────────────────────────────────────
#     🟣 Load Everything in One Go
# 💜────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader and logs memory summary.
    """
    # 🌸 Load Market Alerts
    await load_market_alert_cache(bot)

    # 🌸 Load Missing Pokémon
    await load_missing_pokemon_cache(bot)

    # 🎀 Unified summary log
    pretty_log(
        tag="",
        label="🦋 CENTRAL CACHE",
        message=(
            f"All caches refreshed and loaded "
            f"(Market Alerts: {len(market_alert_cache)} ~{get_deep_size(market_alert_cache)//1024} KB + "
            f"Missing Pokémon: {len(missing_pokemon_cache)} ~{get_deep_size(missing_pokemon_cache)//1024} KB)"
        ),
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
