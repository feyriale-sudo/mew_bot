import discord

from utils.db.battletower_db import fetch_battletower_users
from utils.logs.pretty_log import pretty_log
from utils.cache.cache_list import battle_tower_cache
# 🍡──────────────────────────────────────────────
# Load Battle Tower Cache
# 🍡──────────────────────────────────────────────
async def load_battle_tower_cache(bot):
    """Load all registered Battle Tower users into the cache."""
    try:
        users = await fetch_battletower_users(bot)
        for user in users:
            user_id = user["user_id"]
            battle_tower_cache[user_id] = {
                "user_name": user["user_name"],
                "registered_at": user["registered_at"],
            }
        pretty_log(
            tag="cache",
            message=f"Loaded {len(users)} Battle Tower users into cache.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to load Battle Tower cache: {e}",
            bot=bot,
        )

# 🌸──────────────────────────────────────────────
# Upsert Battle Tower Cache
# 🌸──────────────────────────────────────────────
def upsert_battle_tower_cache(user_id: int, user_name: str, registered_at: int):
    """Upsert a Battle Tower user into the cache."""
    battle_tower_cache[user_id] = {
        "user_name": user_name,
        "registered_at": registered_at,
    }
    pretty_log(
        tag="cache",
        message=f"Upserted Battle Tower user {user_name} ({user_id}) into cache.",
    )

# 🌸──────────────────────────────────────────────
# Remove Battle Tower Cache
# 🌸──────────────────────────────────────────────
def remove_battle_tower_cache(user_id: int):
    """Remove a Battle Tower user from the cache."""
    if user_id in battle_tower_cache:
        del battle_tower_cache[user_id]
        pretty_log(
            tag="cache",
            message=f"Removed Battle Tower user ({user_id}) from cache.",
        )
