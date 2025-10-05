# 🌸──────────────────────────────────────────────
#      💜 Missing Pokémon User Settings DB 💜
# ───────────────────────────────────────────────
import asyncpg
from utils.logs.pretty_log import pretty_log


# ❀─────────────────────────────────────────❀
#      💖 Fetch User Settings Row
# ❀─────────────────────────────────────────❀
async def fetch_user_missing_settings(bot, user_id: int) -> dict | None:
    """
    Fetch the Missing Pokémon settings for a given user.
    Returns None if not found.
    """
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT user_id, user_name, channel_id, role_id
            FROM missing_pokemon_user_settings
            WHERE user_id = $1;
            """,
            user_id,
        )

    if row:
        pretty_log(
            tag="💜 DB",
            label="MISSING SETTINGS",
            message=f"Fetched Missing Pokémon settings for user_id={user_id}",
        )
        return dict(row)
    else:
        pretty_log(
            tag="💜 DB",
            label="MISSING SETTINGS",
            message=f"No Missing Pokémon settings found for user_id={user_id}",
        )
        return None


# ❀─────────────────────────────────────────❀
#      💖 Upsert / Update User Settings
# ❀─────────────────────────────────────────❀
async def upsert_user_missing_settings(
    bot,
    user_id: int,
    user_name: str,
    channel_id: int,
    role_id: int | None = None,
):
    """
    Insert or update a user's Missing Pokémon settings.
    Ensures one row per user_id (PRIMARY KEY).
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO missing_pokemon_user_settings (user_id, user_name, channel_id, role_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id)
            DO UPDATE SET
                user_name = EXCLUDED.user_name,
                channel_id = EXCLUDED.channel_id,
                role_id = EXCLUDED.role_id;
            """,
            user_id,
            user_name,
            channel_id,
            role_id,
        )

    pretty_log(
        tag="💜 DB",
        label="MISSING SETTINGS",
        message=f"Upserted Missing Pokémon settings for {user_name} (channel={channel_id}, role={role_id})",
    )
