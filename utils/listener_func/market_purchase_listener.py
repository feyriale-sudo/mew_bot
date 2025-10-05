import re

import discord

from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member
from utils.db.missing_pokemon_db_func import remove_missing_pokemon
from config.aesthetic import *

# ❀─────────────────────────────────────────❀
#      💖  Market Purchase Listener
# ❀─────────────────────────────────────────❀
async def get_purchased_pokemon(bot, message: discord.Message):
    """
    Extracts the Pokémon name from a PokéMeow purchase message.
    Prints only the Pokémon name (with Shiny/Golden prefix if present).
    """
    content = message.content
    if not content:
        return

    # Look for the Pokémon name between the last bold '**' and 'for <:PokeCoin'
    match = re.search(
        r"\*\*.*?\*\*\s*.*?\*\*\s*(.*?)\s*\*\*\s*for\s+<:PokeCoin", content
    )
    if not match:
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    member_id = member.id
    member_name = member.name

    from utils.cache.missing_pokemon_cache import (
        find_pokemon_in_user_cache_single
    )
    pokemon_name = match.group(1).strip()

    cache_entry = find_pokemon_in_user_cache_single(member_id, pokemon_name)
    if not cache_entry:
        return

    # Remove from Missing List in DB
    await remove_missing_pokemon(bot, member, cache_entry["dex"])
    pretty_log(
        tag="missing",
        message=f"Removed {cache_entry['pokemon_name']} (Dex {cache_entry['dex']}) for user {member_name} ({member_id}) from missing list, as it was purchased.",
    )
    # Optionally react to the original message if it's a reply
    if message.reference and message.reference.resolved:
        await message.reference.resolved.add_reaction(Emojis.Pink_Check)
