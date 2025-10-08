import re

import discord

from config.aesthetic import *
from utils.db.missing_pokemon_db_func import remove_missing_pokemon
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member


# ❀─────────────────────────────────────────❀
#      💖  Dex Listener
# ❀─────────────────────────────────────────❀
async def dex_message_handler(bot, message: discord.Message):
    """
    Extracts the Pokémon name from a PokéMeow dex message,
    checks if it's in the user's missing list, and removes it if they now own it.
    """

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    author_name = embed.author.name
    if not author_name:
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    member_id = member.id
    match = re.match(r"^(.+?)\s+#(\d+)$", author_name)
    if not match:
        return

    pokemon_name = match.group(1).strip()
    dex_number = match.group(2).strip()
    if not pokemon_name or not dex_number:
        return

    from utils.cache.missing_pokemon_cache import (
        find_pokemon_in_user_cache_single,
        remove_missing,
    )

    cache_entry = find_pokemon_in_user_cache_single(member_id, pokemon_name)
    if not cache_entry:
        return

    # 🌸────────────────────────────────────────────
    # [💜 CHECK] If the user now owns this Pokémon
    # 🌸────────────────────────────────────────────
    try:
        # Look for the "Owned" field which contains the count
        owned_count = 0
        for field in embed.fields:
            if "Owned" in field.name:
                # Extract number from field value (remove emojis and get the number)
                owned_value = field.value
                # Remove Discord emoji format and extract numbers
                cleaned_value = re.sub(r"<a?:\w+:\d+>", "", owned_value)
                # Extract number (could be formatted with commas)
                number_match = re.search(r"(\d[\d,]*)", cleaned_value)
                if number_match:
                    owned_count = int(number_match.group(1).replace(",", ""))
                break


        # If owned count > 0, remove from missing list
        if owned_count > 0:

            # Remove from database
            await remove_missing_pokemon(bot, member, int(dex_number))

            # Add reaction to the dex message
            await message.add_reaction(Emojis.Pink_Check)
            # Add reaction to the original message
            replied_to_message = (
                message.reference.resolved if message.reference else None
            )
            if replied_to_message:
                await replied_to_message.add_reaction(Emojis.Pink_Check)

            pretty_log(
                "db",
                f"[💎 REMOVED] {pokemon_name} (#{dex_number}) removed from {member.display_name}'s missing list (owned: {owned_count:,}).",
            )
        else:
            pretty_log(
                "debug",
                f"[⏭️ SKIP] {pokemon_name} (#{dex_number}) - User doesn't own any yet (owned: {owned_count}).",
            )

    except Exception as e:
        pretty_log(
            "error",
            f"[⚠️ DEX HANDLER ERROR] Failed to process dex for {pokemon_name}: {e}",
            include_trace=True,
        )
