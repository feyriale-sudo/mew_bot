import discord
from utils.pokemeow.autocomplete import format_display_name
from utils.logs.pretty_log import pretty_log
# ❀─────────────────────────────────────────❀
#      💖  User Entries Autocomplete
# ❀─────────────────────────────────────────❀
async def user_missing_pokemon_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    """
    Autocomplete for the user's own missing Pokémon from cache.
    Choice.name = "Name #Dex"
    Choice.value = "Dex" only (as string)
    Matches both names and dex numbers.
    """
    from utils.cache.missing_pokemon_cache import fetch_user_missing_from_cache


    user_id = interaction.user.id
    try:
        rows = fetch_user_missing_from_cache(user_id)
    except Exception:
        rows = []

    current = (current or "").lower().strip()
    results: list[discord.app_commands.Choice[str]] = []

    # Check if input is numeric
    dex_query = None
    if current.isdigit():
        try:
            dex_query = int(current)
        except ValueError:
            dex_query = None

    for row in rows:
        raw_name = row["pokemon_name"]
        name = format_display_name(raw_name)
        dex = row.get("dex")

        display = f"{name} #{dex}"

        if (
            not current
            or current in name.lower()
            or (dex is not None and current in str(dex))
            or (dex_query is not None and dex_query == dex)
        ):
            results.append(discord.app_commands.Choice(name=display.title(), value=str(dex)))

        if len(results) >= 25:
            break

    if not results:
        results.append(
            discord.app_commands.Choice(name="No matches found", value=current or "")
        )

    return results
# ❀─────────────────────────────────────────❀
#      💖  Upsert Missing Pokémon
# ❀─────────────────────────────────────────❀
async def upsert_missing_pokemon(
    bot,
    user_id: int,
    user_name: str,
    dex: int,
    pokemon_name: str,
    role_id: int | None = None,
    channel_id: int | None = None,
):
    """
    Insert or update a missing Pokémon for a user.
    Ensures one row per (user_id, dex) due to UNIQUE constraint.
    """
    from utils.cache.missing_pokemon_cache import insert_missing

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO missing_pokemon (user_id, user_name, dex, pokemon_name, role_id, channel_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, dex)
            DO UPDATE SET
                user_name = EXCLUDED.user_name,
                pokemon_name = EXCLUDED.pokemon_name,
                role_id = EXCLUDED.role_id,
                channel_id = EXCLUDED.channel_id;
            """,
            user_id,
            user_name,
            dex,
            pokemon_name,
            role_id,
            channel_id,
        )

        pretty_log(
            tag="💜 DB",
            message=f"Inserted/Updated missing Pokémon for {user_name}: dex={dex}, name={pokemon_name}, role_id={role_id}, channel_id={channel_id}",
        )

        # Update cache
        new_entry = {
            "user_id": user_id,
            "user_name": user_name,
            "dex": dex,
            "pokemon_name": pokemon_name,
            "role_id": role_id,
            "channel_id": channel_id,
        }
        insert_missing(new_entry)


# ❀─────────────────────────────────────────❀
#      💖  Bulk Upsert Missing Pokémon
# ❀─────────────────────────────────────────❀
async def bulk_upsert_missing_pokemon(bot, entries: list[dict]):
    """
    Bulk insert or update missing Pokémon.
    Each entry should be a dict with keys:
    user_id, user_name, dex, pokemon_name, role_id (optional), channel_id (optional)
    """
    if not entries:
        return

    values_str_list = []
    params = []

    for i, entry in enumerate(entries):
        idx = i * 6  # ✅ now 6 parameters per entry
        values_str_list.append(
            f"(${idx+1}, ${idx+2}, ${idx+3}, ${idx+4}, ${idx+5}, ${idx+6})"
        )
        params.extend(
            [
                entry.get("user_id"),
                entry.get("user_name"),
                entry.get("dex"),
                entry.get("pokemon_name"),
                entry.get("role_id"),
                entry.get("channel_id"),
            ]
        )

    values_str = ", ".join(values_str_list)

    query = f"""
    INSERT INTO missing_pokemon (user_id, user_name, dex, pokemon_name, role_id, channel_id)
    VALUES {values_str}
    ON CONFLICT (user_id, dex)
    DO UPDATE SET
        user_name = EXCLUDED.user_name,
        pokemon_name = EXCLUDED.pokemon_name,
        role_id = EXCLUDED.role_id,
        channel_id = EXCLUDED.channel_id;
    """

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, *params)

        pretty_log(
            tag="💜 DB",
            message=f"Bulk inserted/updated {len(entries)} missing Pokémon entries (includes role_id & channel_id).",
        )

        from utils.cache.missing_pokemon_cache import bulk_upsert_missing_pokemon_cache

        bulk_upsert_missing_pokemon_cache(entries)

        pretty_log(
            tag="💜 CACHE",
            message=f"Bulk upserted {len(entries)} missing Pokémon entries into cache (includes role_id & channel_id).",
        )


# ❀─────────────────────────────────────────❀
#      💖  Update Missing Pokémon
# ❀─────────────────────────────────────────❀
async def update_missing_pokemon(
    bot,
    user_id: int,
    dex: int,
    new_pokemon_name: str,
    new_role_id: int | None = None,
    new_channel_id: int | None = None,
):
    """
    Update the Pokémon name (and optionally role_id & channel_id) for a given user and dex number.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE missing_pokemon
            SET
                pokemon_name = $1,
                role_id = $2,
                channel_id = $3
            WHERE user_id = $4 AND dex = $5;
            """,
            new_pokemon_name,
            new_role_id,
            new_channel_id,
            user_id,
            dex,
        )

        pretty_log(
            tag="💜 DB",
            message=f"Updated missing Pokémon for user_id={user_id}, dex={dex} → name={new_pokemon_name}, role_id={new_role_id}, channel_id={new_channel_id}",
        )

        # Update cache
        from utils.cache.missing_pokemon_cache import insert_missing

        new_entry = {
            "user_id": user_id,
            "dex": dex,
            "pokemon_name": new_pokemon_name,
            "role_id": new_role_id,
            "channel_id": new_channel_id,
        }
        insert_missing(new_entry)


# ❀─────────────────────────────────────────❀
#      💖  Remove All Missing Pokémon for User
# ❀─────────────────────────────────────────❀
# Remove all missing Pokémon entries for a user
async def remove_all_missing_for_user(bot, user: discord.Member):
    """
    Remove all missing Pokémon entries for a user.
    """
    user_id = user.id
    user_name = user.name

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM missing_pokemon
            WHERE user_id = $1;
            """,
            user_id,
        )
        pretty_log(
            tag="💜 DB",
            message=f"Removed all missing Pokémon for {user_name} (user_id={user_id})",
        )

        # Remove all from cache as well
        from utils.cache.missing_pokemon_cache import remove_all_missing_for_user_cache

        remove_all_missing_for_user_cache(user_id)


# ❀─────────────────────────────────────────❀
#      💖  Remove Missing Pokemon
# ❀─────────────────────────────────────────❀
# Remove a Pokémon entry for a user
async def remove_missing_pokemon(bot, user: discord.Member, dex: int):
    """
    Remove a missing Pokémon entry for a user by dex.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM missing_pokemon
            WHERE user_id = $1 AND dex = $2;
            """,
            user_id,
            dex,
        )
        pretty_log(
            tag="💜 DB",
            message=f"Removed missing Pokémon for {user_name}, dex={dex}",
        )
        # Remove from cache as well
        from utils.cache.missing_pokemon_cache import remove_missing
        remove_missing(user_id, dex)


# ❀─────────────────────────────────────────❀
#      💖  Fetch User Missing Pokemon
# ❀─────────────────────────────────────────❀
# Fetch one Pokémon entry for a user (by dex)
async def fetch_user_missing_pokemon(bot, user:discord.Member, dex: int):
    """
    Fetch a single missing Pokémon row for a user by dex.
    Returns None if not found.
    """
    user_id = user.id
    user_name = user.name
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT * FROM missing_pokemon
            WHERE user_id = $1 AND dex = $2;
            """,
            user_id,
            dex,
        )


# ❀─────────────────────────────────────────❀
#      💖  Fetch All User Missing
# ❀─────────────────────────────────────────❀
# Fetch all missing Pokémon for a user
async def fetch_all_user_missing(bot, user_id: int):
    """
    Fetch all missing Pokémon rows for a specific user.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM missing_pokemon
            WHERE user_id = $1
            ORDER BY dex ASC;
            """,
            user_id,
        )


# ❀─────────────────────────────────────────❀
#      💖  Fetch All Missing
# ❀─────────────────────────────────────────❀
# Fetch all missing Pokémon for all users
async def fetch_all_missing(bot):
    """
    Fetch all missing Pokémon entries in the database.
    """
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT * FROM missing_pokemon
            ORDER BY user_id ASC, dex ASC;
            """
        )


# ❀─────────────────────────────────────────❀
#      💖  Fetch User Missing Dict
# ❀─────────────────────────────────────────❀
async def fetch_user_missing_dict(bot, user_id: int) -> dict[int, str]:
    """
    Fetch all missing Pokémon for a user and return as a dictionary.

    Returns:
        dict: {dex: pokemon_name, ...}
    """
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT dex, pokemon_name
            FROM missing_pokemon
            WHERE user_id = $1
            ORDER BY dex ASC;
            """,
            user_id,
        )

    # Convert to {dex: pokemon_name}
    return {row["dex"]: row["pokemon_name"] for row in rows}


# ❀─────────────────────────────────────────❀
#      💖  Fetch User Missing Pokémon (List)
# ❀─────────────────────────────────────────❀
async def fetch_user_missing_list(bot, user_id: int) -> list[dict]:
    """
    Fetch all missing Pokémon for a user and return as a list of dicts.

    Returns:
        list[dict]: [{"dex": int, "pokemon_name": str}, ...]
    """
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT dex, pokemon_name
            FROM missing_pokemon
            WHERE user_id = $1
            ORDER BY dex ASC;
            """,
            user_id,
        )

    results = [{"dex": row["dex"], "pokemon_name": row["pokemon_name"]} for row in rows]

    pretty_log(
        tag="💜 CACHE",
        label="USER MISSING FETCH",
        message=f"Fetched {len(results)} missing Pokémon entries for user_id={user_id}. 🌸",
    )
    return results
