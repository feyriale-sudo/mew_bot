# 🟣────────────────────────────────────────────
#           💜 Missing Pokémon Cache Loader 💜
# ─────────────────────────────────────────────

import sys

from utils.cache.cache_list import _missing_pokemon_index, missing_pokemon_cache
from utils.db.missing_pokemon_db_func import fetch_all_missing
from utils.logs.pretty_log import pretty_log


# ❀─────────────────────────────────────────❀
#      💖 Load Missing Pokémon Cache
# ❀─────────────────────────────────────────❀
async def load_missing_pokemon_cache(bot):
    """Load all missing Pokémon from DB into cache."""
    missing_pokemon_cache.clear()
    _missing_pokemon_index.clear()

    all_missing = await fetch_all_missing(bot)

    for row in all_missing:
        entry = {
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "dex": row["dex"],
            "pokemon_name": row["pokemon_name"],
            "channel_id": row.get("channel_id"),  # 🆕 Added
            "role_id": row.get("role_id"),  # 🆕 Added
        }
        missing_pokemon_cache.append(entry)
        key = (entry["user_id"], entry["dex"])
        _missing_pokemon_index[key] = entry

    pretty_log(
        tag="missing",
        message=f"Loaded {len(missing_pokemon_cache)} missing Pokémon into cache",
    )
    return missing_pokemon_cache


# ❀─────────────────────────────────────────❀
#      💖 Check if Pokémon Exists for User (Cache)
# ❀─────────────────────────────────────────❀
def is_pokemon_in_user_cache(user_id: int, pokemon_name: str) -> bool:
    """
    Check if a Pokémon (case-insensitive) exists in the cache for a given user.

    Returns:
        bool: True if Pokémon found for user, False otherwise.
    """
    target = pokemon_name.strip().lower()

    for entry in missing_pokemon_cache:
        if (
            entry.get("user_id") == user_id
            and entry.get("pokemon_name", "").lower() == target
        ):
            pretty_log(
                tag="missing",
                label="POKÉMON CHECKER",
                message=f"Found '{pokemon_name}' in cache for user_id={user_id} 💖",
            )
            return True

    pretty_log(
        tag="missing",
        label="POKÉMON CHECKER",
        message=f"'{pokemon_name}' not found in cache for user_id={user_id} 💧",
    )
    return False


# ❀─────────────────────────────────────────❀
#      💖 Find Pokemon in (User Cache)
# ❀─────────────────────────────────────────❀
def find_pokemon_in_user_cache(user_id: int, pokemon_name: str) -> list[dict]:
    """
    Fetch all cache entries matching a Pokémon name (case-insensitive) for a specific user.
    Returns a list of matching dict entries.
    """
    target = pokemon_name.strip().lower()
    matches = [
        e
        for e in missing_pokemon_cache
        if e.get("user_id") == user_id and e.get("pokemon_name", "").lower() == target
    ]

    pretty_log(
        tag="missing",
        message=f"Found {len(matches)} entries for '{pokemon_name}' (user_id={user_id}) 🌸",
    )
    return matches


# ❀─────────────────────────────────────────❀
#      💖 Find Pokémon in (User Cache, Single)
# ❀─────────────────────────────────────────❀
def find_pokemon_in_user_cache_single(user_id: int, pokemon_name: str) -> dict | None:
    """
    Fetch a single Pokémon entry (case-insensitive) for a specific user.
    Returns the matching dict if found, otherwise None.
    """
    target = pokemon_name.strip().lower()

    for entry in missing_pokemon_cache:
        if (
            entry.get("user_id") == user_id
            and entry.get("pokemon_name", "").lower() == target
        ):
            pretty_log(
                tag="missing",
                label="POKÉMON CHECKER",
                message=f"Found '{pokemon_name}' in cache for user_id={user_id} 🌸",
            )
            return entry

    pretty_log(
        tag="missing",
        label="POKÉMON CHECKER",
        message=f"No match for '{pokemon_name}' in cache for user_id={user_id} 💧",
    )
    return None


# ❀─────────────────────────────────────────❀
#      💖 Bulk Insert/Update Missing Pokémon Cache
# ❀─────────────────────────────────────────❀
def bulk_upsert_missing_pokemon_cache(entries: list[dict]):
    """
    Bulk insert or update missing Pokémon in cache only.
    Each entry should include:
    user_id, user_name, dex, pokemon_name, channel_id, role_id
    """
    if not entries:
        return

    for entry in entries:
        key = (entry["user_id"], entry["dex"])
        existing = _missing_pokemon_index.get(key)

        if existing:
            # Update existing cache entry
            existing.update(entry)
            for i, e in enumerate(missing_pokemon_cache):
                if e["user_id"] == entry["user_id"] and e["dex"] == entry["dex"]:
                    missing_pokemon_cache[i] = existing
                    break
        else:
            missing_pokemon_cache.append(entry)
            _missing_pokemon_index[key] = entry


# ❀─────────────────────────────────────────❀
#      💖 Insert / Update Missing Pokémon
# ❀─────────────────────────────────────────❀
def insert_missing(entry: dict):
    """Insert or update a missing Pokémon entry in the cache."""
    key = (entry["user_id"], entry["dex"])
    existing = _missing_pokemon_index.get(key)

    if existing:
        existing.update(entry)
        for i, e in enumerate(missing_pokemon_cache):
            if e["user_id"] == entry["user_id"] and e["dex"] == entry["dex"]:
                missing_pokemon_cache[i] = existing
                break
        pretty_log(
            tag="missing",
            message=f"Updated missing Pokémon for {entry['user_name']} (Dex {entry['dex']})",
        )
    else:
        missing_pokemon_cache.append(entry)
        _missing_pokemon_index[key] = entry
        pretty_log(
            tag="missing",
            message=f"Inserted missing Pokémon for {entry['user_name']} (Dex {entry['dex']})",
        )


# ❀─────────────────────────────────────────❀
#      💖 Remove All Missing Pokémon for User (Cache)
# ❀─────────────────────────────────────────❀
def remove_all_missing_for_user_cache(user_id: int):
    """Remove all missing Pokémon entries for a user from the cache."""
    missing_pokemon_cache[:] = [
        e for e in missing_pokemon_cache if e["user_id"] != user_id
    ]

    keys_to_remove = [k for k in _missing_pokemon_index if k[0] == user_id]
    for key in keys_to_remove:
        _missing_pokemon_index.pop(key, None)

    pretty_log(
        tag="missing",
        message=f"Removed all missing Pokémon from cache for user_id={user_id}",
    )


# ❀─────────────────────────────────────────❀
#      💖 Remove Missing Pokémon
# ❀─────────────────────────────────────────❀
def remove_missing(user_id: int, dex: int):
    """Remove a missing Pokémon from cache."""
    key = (user_id, dex)
    removed_any = False

    missing_pokemon_cache[:] = [
        e
        for e in missing_pokemon_cache
        if not (e["user_id"] == user_id and e["dex"] == dex)
    ]

    if key in _missing_pokemon_index:
        _missing_pokemon_index.pop(key)
        removed_any = True

    msg = (
        f"Removed missing Pokémon (Dex {dex}) for user {user_id}"
        if removed_any
        else f"No missing Pokémon found to remove (Dex {dex}) for user {user_id}"
    )
    pretty_log(tag="missing", message=msg)


# ❀─────────────────────────────────────────❀
#      💖 Get Missing Pokémon (Single)
# ❀─────────────────────────────────────────❀
def get_missing(user_id: int, dex: int) -> dict | None:
    """Fetch a single missing Pokémon entry by user and dex."""
    return _missing_pokemon_index.get((user_id, dex))


# ❀─────────────────────────────────────────❀
#      💖 Fetch All User Missing from Cache
# ❀─────────────────────────────────────────❀
def fetch_user_missing_from_cache(user_id: int) -> list[dict]:
    """Fetch all missing Pokémon for a specific user."""
    return [e for e in missing_pokemon_cache if e["user_id"] == user_id]


# ❀─────────────────────────────────────────❀
#      💖 Fetch All Missing from Cache
# ❀─────────────────────────────────────────❀
def fetch_all_missing_from_cache() -> list[dict]:
    """Fetch all missing Pokémon in cache."""
    return missing_pokemon_cache


# ❀─────────────────────────────────────────❀
#      💖 Cache Memory Size Helper
# ❀─────────────────────────────────────────❀
def get_cache_size(cache: list) -> int:
    """Estimate memory size of the cache in bytes."""
    total = sys.getsizeof(cache)
    for entry in cache:
        total += sys.getsizeof(entry)
        for k, v in entry.items():
            total += sys.getsizeof(k) + sys.getsizeof(v)
    return total
