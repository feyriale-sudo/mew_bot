import discord
from utils.cache.cache_list import utility_cache
from utils.logs.pretty_log import pretty_log
from utils.db.utilities_db_func import fetch_all_utilities


# 🟣────────────────────────────────────────────
#        Utility Cache Loader
# ─────────────────────────────────────────────
async def load_utility_cache(bot):
    """
    Load all user utility settings into memory cache.
    Uses the fetch_all_utilities DB function.
    """
    utility_cache.clear()

    rows = await fetch_all_utilities(bot)
    for row in rows:
        utility_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "fish_rarity": row.get("fish_rarity"),
        }

    # 🐭 Debug log
    pretty_log(
        tag="",
        message=f"Loaded {len(utility_cache)} users' utility settings into cache",
        label="👚 UTILITY CACHE",
        bot=bot,
    )

    return utility_cache

# --------------------
#  Set or update user utility settings
# --------------------
def set_user_utility_cached(
    user_id: int,
    user_name: str | None = None,
    fish_rarity: str | None = None,
):
    """
    Cached version of set_user_utility that updates cache.
    Only fields provided (not None) will be updated.
    """

    try:
        # 🔹 Update cache first
        if user_id not in utility_cache:
            utility_cache[user_id] = {
                "user_name": None,
                "fish_rarity": None,
            }

        if user_name is not None:
            utility_cache[user_id]["user_name"] = user_name
        if fish_rarity is not None:
            utility_cache[user_id]["fish_rarity"] = fish_rarity


        pretty_log(
            tag="cache",
            message=f"Set utility settings for user {user_id} in cache",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set utility settings for user {user_id}: {e}",
        )

# --------------------
#  Update fish_rarity in cache
# --------------------
def update_fish_rarity_in_cache(user: discord.Member, fish_rarity: str):
    """
    Update only the fish_rarity field for a user in the utility cache.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        if user_id in utility_cache:
            utility_cache[user_id]["fish_rarity"] = fish_rarity
            user_name = utility_cache[user_id].get("user_name")
            pretty_log(
                tag="cache",
                message=f"Updated fish_rarity for {user_name} in cache",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"{user_name} not found in utility cache to update fish_rarity",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update fish_rarity for {user_name}: {e}",
        )


# --------------------
#  Delete user utility from cache
# --------------------
def delete_user_utility_from_cache(user:discord.Member):
    """
    Remove a user's utility settings from the cache.
    """
    user_id = user.id
    user_name = user.display_name
    try:
        if user_id in utility_cache:
            del utility_cache[user_id]
            pretty_log(
                tag="cache",
                message=f"Deleted utility settings for {user_name} from cache",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"{user_name} not found in utility cache to delete",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete utility settings for {user_name} from cache: {e}",
        )
