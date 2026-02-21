import re

import discord

from config.aesthetic import *
from utils.db.missing_pokemon_db_func import remove_missing_pokemon
from utils.logs.debug_logs import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member
from utils.functions.pokemon_func import is_mon_exclusive
from utils.db.market_value_db_func import (
    fetch_dex_number_cache,
    fetch_image_link_cache,
    fetch_pokemon_exclusivity_cache,
    update_dex_number,
    update_is_exclusive,
    upsert_image_link,
)

# enable_debug(f"{__name__}.dex_message_handler")


def extract_pokemon_name_and_dex(text):
    match = re.match(r"(.+?)\s*#(\d+)", text)
    if match:
        name = match.group(1).strip()
        dex = match.group(2).strip()
        return name, dex
    else:
        return text.strip(), None


# ❀─────────────────────────────────────────❀
#      💖  Dex Listener
# ❀─────────────────────────────────────────❀
async def dex_message_handler(bot, message: discord.Message):
    """
    Extracts the Pokémon name from a PokéMeow dex message,
    checks if it's in the user's missing list, and removes it if they now own it.
    """

    embed = message.embeds[0] if message.embeds else None
    debug_log(f"embed: {embed}")
    if not embed:
        debug_log("No embed found in message.")
        return

    author_name = embed.author.name
    debug_log(f"embed.author.name: {author_name}")
    if not author_name:
        debug_log("No author name in embed.")
        return

    # Update Image and Name Caches if needed
    embed_title = embed.title if embed.title else ""
    embed_author_name = embed.author.name if embed.author else ""
    pokemon_name, dex_number = extract_pokemon_name_and_dex(embed_author_name)
    if not pokemon_name:
        debug_log(
            f"Could not extract pokemon name from embed title: '{embed_author_name}'"
        )
        return
    embed_image_url = embed.image.url if embed.image else None
    image_link_cache = fetch_image_link_cache(pokemon_name)
    existing_exclusive_status = fetch_pokemon_exclusivity_cache(pokemon_name)
    is_exclusive = is_mon_exclusive(pokemon_name)
    if existing_exclusive_status != is_exclusive and is_exclusive == False:
        new_exclusive = is_exclusive
        await update_is_exclusive(bot, pokemon_name, new_exclusive)
    else:
        new_exclusive = existing_exclusive_status
    if embed_image_url and image_link_cache != embed_image_url:
        await upsert_image_link(bot, pokemon_name, embed_image_url, new_exclusive)
        debug_log(f"Updated image link for {pokemon_name} to {embed_image_url}.")
        pretty_log(
            "info",
            f"Updated image link for {pokemon_name} to {embed_image_url}.",
        )
    old_dex_number = fetch_dex_number_cache(pokemon_name)
    if dex_number and str(old_dex_number) != str(dex_number):
        dex_number = int(dex_number)
        await update_dex_number(bot, pokemon_name, dex_number)
        debug_log(f"Updated dex number for {pokemon_name} to {dex_number}.")
        pretty_log(
            "info",
            f"Updated dex number for {pokemon_name} to {dex_number}.",
        )

    member = await get_pokemeow_reply_member(message)
    debug_log(f"member: {member}")
    if not member:
        debug_log(
            f"Could not find member from PokéMeow reply in {message.channel.name}"
        )
        return

    member_id = member.id
    debug_log(f"member_id: {member_id}")
    match = re.match(r"^(.+?)\s+#(\d+)$", author_name)
    debug_log(f"match: {match}")
    if not match:
        debug_log(
            f"Author name did not match expected pattern: {author_name}"
        )
        return

    pokemon_name = match.group(1).strip()
    dex_number = match.group(2).strip()
    debug_log(f"pokemon_name: {pokemon_name}, dex_number: {dex_number}")
    if not pokemon_name or not dex_number:
        debug_log(
            f"Missing pokemon_name or dex_number. pokemon_name: {pokemon_name}, dex_number: {dex_number}"
        )
        return

    from utils.cache.missing_pokemon_cache import (
        find_pokemon_in_user_cache_single,
        remove_missing,
    )

    cache_entry = find_pokemon_in_user_cache_single(member_id, pokemon_name)
    debug_log(f"cache_entry: {cache_entry}")
    if not cache_entry:
        debug_log(
            f"No cache entry for {pokemon_name} and user {member_id}"
        )
        return

    # 🌸────────────────────────────────────────────
    # [💜 CHECK] If the user now owns this Pokémon
    # 🌸────────────────────────────────────────────
    try:
        # Look for the "Owned" field which contains the count
        owned_count = 0
        debug_log(f"embed.fields: {embed.fields}")
        for field in embed.fields:
            debug_log(f"Checking field: {field.name} = {field.value}")
            if "Owned" in field.name:
                # Extract number from field value (remove emojis and get the number)
                owned_value = field.value
                debug_log(f"owned_value: {owned_value}")
                # Remove Discord emoji format and extract numbers
                cleaned_value = re.sub(r"<a?:\w+:\d+>", "", owned_value)
                debug_log(f"cleaned_value: {cleaned_value}")
                # Extract number (could be formatted with commas)
                number_match = re.search(r"(\d[\d,]*)", cleaned_value)
                debug_log(f"number_match: {number_match}")
                if number_match:
                    owned_count = int(number_match.group(1).replace(",", ""))
                    debug_log(f"owned_count parsed: {owned_count}")
                break

        debug_log(f"Final owned_count: {owned_count}")

        # If owned count > 0, remove from missing list
        if owned_count > 0:
            debug_log(f"owned_count > 0, removing from missing list.")
            # Remove from database
            await remove_missing_pokemon(bot, member, int(dex_number))

            # Add reaction to the dex message
            await message.add_reaction(Emojis.Pink_Check)
            # Add reaction to the original message
            replied_to_message = (
                message.reference.resolved if message.reference else None
            )
            debug_log(f"replied_to_message: {replied_to_message}")
            if replied_to_message:
                await replied_to_message.add_reaction(Emojis.Pink_Check)

            pretty_log(
                "db",
                f"[💎 REMOVED] {pokemon_name} (#{dex_number}) removed from {member.display_name}'s missing list (owned: {owned_count:,}).",
            )
        else:
            debug_log(f"owned_count == 0, skipping removal.")
            pretty_log(
                "debug",
                f"[⏭️ SKIP] {pokemon_name} (#{dex_number}) - User doesn't own any yet (owned: {owned_count}).",
            )

    except Exception as e:
        debug_log(f"Exception: {e}")
        pretty_log(
            "error",
            f"[⚠️ DEX HANDLER ERROR] Failed to process dex for {pokemon_name}: {e}",
            include_trace=True,
        )
