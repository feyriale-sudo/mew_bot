import re
import discord

from config.aesthetic import Emojis
from utils.db.missing_pokemon_db_func import remove_missing_pokemon
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member
from utils.cache.missing_pokemon_cache import (
    find_pokemon_in_user_cache_single,
    remove_missing,
)


# ❀─────────────────────────────────────────❀
#      💖  Single Trade Listener (PokéMeow)
# ❀─────────────────────────────────────────❀
async def handle_single_trade_message(bot, message: discord.Message):
    """
    Detects PokéMeow trade messages and removes Pokémon from a receiver's missing list
    if they receive a Pokémon that was previously marked missing.
    """
    content = message.content
    if not content or ":handshake:" not in content:
        return

    # 🎀 Regex: Capture Receiver + Pokémon name
    trade_pattern = re.compile(
        r"(?P<receiver>(?:<@!\d+>|:\w+:)? ?\w+(?:\.\w+|_\w+)?(?: \w+)?) received a\s+(?:[:<][^:>]+[:>]?\s*)*(?P<pokemon>[A-Za-zéÉ'\-\.]+)\s+from",
        re.IGNORECASE,
    )
    matches = trade_pattern.findall(content)
    if not matches:
        return

    # 🩵 Process each trade in the message
    for receiver_name, pokemon_name in matches:
        pokemon_name = pokemon_name.strip()
        pretty_log(
            tag="💜 TRADE",
            label="CHECK",
            message=f"{receiver_name} received {pokemon_name} — checking missing cache...",
        )

        # 💬 Try to find the Discord member who received it
        receiver_member = await get_pokemeow_reply_member(message)
        if not receiver_member:
            pretty_log(
                tag="⚪ TRADE",
                label="SKIP",
                message=f"Could not resolve Discord member for receiver '{receiver_name}'.",
            )
            continue

        receiver_id = receiver_member.id

        # 💾 Check if Pokémon is in their missing cache
        cache_entry = find_pokemon_in_user_cache_single(receiver_id, pokemon_name)
        if not cache_entry:
            pretty_log(
                tag="💜 TRADE",
                label="NO MATCH",
                message=f"{receiver_name} did not have {pokemon_name} in their missing list.",
            )
            continue

        # 🧹 Remove from cache + DB
        try:
            remove_missing(receiver_id, cache_entry["dex"])  # from cache
            await remove_missing_pokemon(receiver_id, cache_entry["dex"])  # from DB
            pretty_log(
                tag="💜 TRADE",
                label="REMOVED",
                message=f"Removed {pokemon_name} (Dex {cache_entry['dex']}) from {receiver_name}'s missing list (received in trade).",
            )
        except Exception as e:
            pretty_log(
                tag="❌ TRADE",
                label="ERROR",
                message=f"Failed to remove {pokemon_name} for {receiver_name}: {e}",
            )

    # 💠 Optional: Add emoji reaction for visual feedback
    if message.reference and message.reference.resolved:
        await message.reference.resolved.add_reaction(Emojis.Pink_Check)
