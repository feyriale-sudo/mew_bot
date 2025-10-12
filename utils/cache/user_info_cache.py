import discord

from utils.cache.cache_list import user_info_cache  # 💜 import your cache
from utils.db.user_info_db_func import fetch_all_user_info
from utils.logs.pretty_log import pretty_log


# 💜────────────────────────────────────────────
#        User Info Cache Loader
# ─────────────────────────────────────────────
async def load_user_info_cache(bot):
    """
    Load all user info data into memory cache.
    Uses the fetch_all_user_info DB function.
    """
    user_info_cache.clear()  # Clear existing cache

    rows = await fetch_all_user_info(bot)
    for row in rows:
        user_info_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "faction": row.get("faction"),
            "patreon_tier": row.get("patreon_tier"),
        }

    # 🐭 Debug log
    pretty_log(
        tag="",
        message=f"Loaded {len(user_info_cache)} users' info into cache",
        label="🩰 USER INFO CACHE",
        bot=bot,
    )

    return user_info_cache

# --------------------
#  Set or update user info
# --------------------
def set_user_info_cached(
    user_id: int,
    user_name: str | None = None,
    faction: str | None = None,
    patreon_tier: str | None = None,
):
    """
    Cached version of set_user_info that updates cache.
    Only fields provided (not None) will be updated.
    """

    try:
        # 🔹 Update cache first
        if user_id not in user_info_cache:
            user_info_cache[user_id] = {
                "user_name": None,
                "faction": None,
                "patreon_tier": None,
            }

        if user_name is not None:
            user_info_cache[user_id]["user_name"] = user_name
        if faction is not None:
            user_info_cache[user_id]["faction"] = faction
        if patreon_tier is not None:
            user_info_cache[user_id]["patreon_tier"] = patreon_tier

        pretty_log(
            tag="cache",
            message=f"Updated user info cache for {user_name}",
            label="🩰 USER INFO CACHE",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set user info in cache for user {user_id}: {e}",
        )

# --------------------
#  Update faction in cache
# --------------------
def update_faction_in_cache(user: discord.Member, faction: str):
    """
    Update a user's faction in cache.
    """
    try:
        if user.id in user_info_cache:
            user_info_cache[user.id]["faction"] = faction
            pretty_log(
                tag="cache",
                message=f"Updated faction in cache for {user.display_name} to {faction}",
                label="🩰 USER INFO CACHE",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"User {user.display_name} not found in cache to update faction.",
                label="🩰 USER INFO CACHE",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update faction in cache for {user.display_name}: {e}",
        )

# --------------------
#  Update patreon_tier in cache
# --------------------
def update_patreon_tier_in_cache(user: discord.Member, patreon_tier: str):
    """
    Update a user's patreon_tier in cache.
    """
    try:
        if user.id in user_info_cache:
            user_info_cache[user.id]["patreon_tier"] = patreon_tier
            pretty_log(
                tag="cache",
                message=f"Updated patreon_tier in cache for {user.display_name} to {patreon_tier}",
                label="🩰 USER INFO CACHE",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"User {user.display_name} not found in cache to update patreon_tier.",
                label="🩰 USER INFO CACHE",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update patreon_tier in cache for {user.display_name}: {e}",
        )

# --------------------
#  Update user name in cache
# --------------------
def update_user_name_in_cache(user: discord.Member, user_name: str):
    """
    Update a user's name in cache.
    """
    try:
        if user.id in user_info_cache:
            user_info_cache[user.id]["user_name"] = user_name
            pretty_log(
                tag="cache",
                message=f"Updated user_name in cache for {user.display_name} to {user_name}",
                label="🩰 USER INFO CACHE",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"User {user.display_name} not found in cache to update user_name.",
                label="🩰 USER INFO CACHE",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update user_name in cache for {user.display_name}: {e}",
        )

#--------------------
#  Delete user info from cache
#--------------------
def delete_user_info_from_cache(user:discord.Member):
    """
    Delete a user's info from cache.
    """
    try:
        if user.id in user_info_cache:
            del user_info_cache[user.id]
            pretty_log(
                tag="cache",
                message=f"Deleted user info from cache for {user.display_name}",
                label="🩰 USER INFO CACHE",
            )
        else:
            pretty_log(
                tag="warning",
                message=f"User {user.display_name} not found in cache to delete.",
                label="🩰 USER INFO CACHE",
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete user info from cache for {user.display_name}: {e}",
        )