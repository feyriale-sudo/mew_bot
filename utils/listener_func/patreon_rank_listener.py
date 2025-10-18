import re

import discord

from utils.cache.cache_list import user_info_cache
from utils.db.user_info_db_func import set_user_info, update_patreon_tier
from utils.logs.pretty_log import pretty_log

BANNED_PHRASES = {"PokeMeow Clans — Perks Info", "PokeMeow Clans — Rank Info"}
PATREON_RANKS = {
    "common",
    "uncommon",
    "rare",
    "superrare",
    "legendary",
    "shiny",
    "golden",
}


# 🟣────────────────────────────────────────────
#       🎨 Extract Username from Embed Title
# 🟣────────────────────────────────────────────
def extract_username_from_title(title: str) -> str:
    """
    Extracts the username part from a title like:
    <:emoji:id>**_0rz_** -> _0rz_
    """
    # Remove custom emojis (<:name:id> or <a:name:id>)
    no_emoji = re.sub(r"<a?:\w+:\d+>", "", title)

    # Remove bold/italic markdown (** or __ or *)
    no_format = re.sub(r"[*]{1,2}|_{2}", "", no_emoji)

    # Final cleanup: strip spaces only
    return no_format.strip()


# 🔹────────────────────────────────────────────
#   🏆 Extract Patreon Rank From Perks Embed
# 🔹────────────────────────────────────────────
async def extract_patreon_rank_from_perks_embed(
    bot: discord.Client, message: discord.Message
):
    """
    Updates the user's patreon_tier in the database and cache if it has changed.
    """
    if not message.embeds:
        return None

    embed = message.embeds[0]
    author_text = getattr(embed.author, "name", "")

    # Must not have these phrases
    if author_text in BANNED_PHRASES:
        return

    author_name = embed.author.name or ""  # "khy.09's perks"
    # Remove the "'s perks" suffix
    author_name = author_name.replace("'s perks", "")
    # Now clean lightly if you want
    cleaned_name = re.sub(r"[^\w\d.]", "", author_name)
    # -> "khy.09"

    # Check if user in user info cache
    from utils.cache.user_info_cache import get_user_id_by_name

    user_id = get_user_id_by_name(cleaned_name)
    if user_id:
        user = message.guild.get_member(user_id)
    elif not user_id:
        # Upsert user name to DB and cache
        user = discord.utils.find(
            lambda m: m.name == cleaned_name,
            message.guild.members,
        )
        if user:
            user_id = user.id
            await set_user_info(bot, user_id=user_id, user_name=cleaned_name)
            pretty_log(
                tag="",
                message=f"Upserted user '{cleaned_name}' with ID {user_id} from perks embed",
                label="🏆 PATREON RANK",
                bot=bot,
            )
        else:
            return

    # Check current rank
    user_info = user_info_cache.get(user_id)
    current_patreon_rank = user_info.get("patreon_tier") if user_info else None
    new_patreon_rank = None

    # Extract rank from title
    title = embed.title or ""
    if embed.title and "You are currently a **Player**" in embed.title:
        new_patreon_rank = "no_perks"

    else:
        patreon_rank_match = re.search(r"\*\*(\w+)\s+Patreon\*\*", title)
        new_patreon_rank = patreon_rank_match.group(1)
        new_patreon_rank = new_patreon_rank.lower() if new_patreon_rank else None

    if new_patreon_rank == current_patreon_rank:
        return  # No change

    # Update DB and cache
    await update_patreon_tier(bot, user=user, patreon_tier=new_patreon_rank)


# 🔹────────────────────────────────────────────
#   🏅 Extract Patreon Tier From Pro Embed
# 🔹────────────────────────────────────────────
async def extract_patreon_rank_from_pro_embed(
    bot: discord.Client, message: discord.Message
):
    """
    🔹 Extracts info from a PokéMeow message embed.
    Returns None if user not in straymons DB.
    """
    if not message.embeds:
        return None

    embed = message.embeds[0]
    title = embed.title or ""
    guild = message.guild
    cleaned_name = extract_username_from_title(title)

    # Check if user in user info cache
    from utils.cache.user_info_cache import get_user_id_by_name

    user_id = get_user_id_by_name(cleaned_name)
    if user_id:
        user = guild.get_member(user_id)
    elif not user_id:
        # Upsert user name to DB and cache
        user = discord.utils.find(
            lambda m: m.name == cleaned_name,
            guild.members,
        )
        if user:
            user_id = user.id
            await set_user_info(bot, user_id=user_id, user_name=cleaned_name)
            pretty_log(
                tag="",
                message=f"Upserted user '{cleaned_name}' with ID {user_id} from pro embed",
                label="🏅 PATREON RANK",
                bot=bot,
            )
        else:
            return
    # Check current rank
    user_info = user_info_cache.get(user_id)
    current_patreon_rank = user_info.get("patreon_tier") if user_info else None

    embed_description = embed.description or ""
    new_patreon_rank = None
    if "patreonlogo" not in embed_description:
        new_patreon_rank = "no_perks"
    else:
        match = re.search(r"<:patreonlogo:\d+>\s*<:(\w+):\d+>", embed_description)
        new_patreon_rank = match.group(1)
        new_patreon_rank = new_patreon_rank.lower() if new_patreon_rank else None

    if new_patreon_rank == current_patreon_rank:
        return  # No change

    # Update DB and cache
    await update_patreon_tier(bot, user=user, patreon_tier=new_patreon_rank)
