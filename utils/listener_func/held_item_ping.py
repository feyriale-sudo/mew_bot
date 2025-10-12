import re

import discord

from config.aesthetic import Emojis
from config.held_item import *
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member


# ─────────────────────────────
#  💎 Pretty names for items
# ─────────────────────────────
def pretty_item_name(item: str) -> str:
    """Return the properly formatted item name."""
    return PRETTY_ITEM_NAMES.get(item.lower(), item.title())


# 🌸──────────────────────────────────────────────
#      🎒 Held Item Ping Listener 🎒
# ───────────────────────────────────────────────
async def held_item_ping(message: discord.Message):
    """Detects held item pings in a Discord message."""

    embed = message.embeds[0] if message.embeds else None
    description_text = embed.description if embed else None
    if not description_text:
        return None  # No embed or description, exit early

    user = await get_pokemeow_reply_member(message)
    if not user:
        return None  # Unable to identify user, exit early

    # --- Held item ---
    held_pokemon = None
    # Regex: extract optional held item and Pokemon name
    pattern = (
        r"(?:<:[^:]+:\d+>\s*)?"  # optional leading NPC emoji
        r"\*\*.+?\*\*\s*found a wild\s*"
        r"(?P<teamlogo><:team_logo:\d+>)?\s*"  # optional team logo emoji
        r"(?P<held><:held_item:\d+>)?\s*"  # optional held item emoji
        r"(?:<:[^:]+:\d+>\s*)+"  # Pokemon emoji (+ optional dexCaught)
        r"\*\*(?P<pokemon>[A-Za-z_]+)\*\*"  # pokemon name
    )
    matches = re.finditer(pattern, description_text)
    for match in matches:
        pokemon_name = match.group("pokemon").lower()
        has_held_item = bool(match.group("held"))

        if not has_held_item:
            continue
        msg = held_item_message(pokemon_name)

        if not msg:
            continue

        try:
            content = f"{user.mention} {msg}"
            await message.channel.send(content=content)
            pretty_log(
                "sent",
                f"Sent held item ping for {pokemon_name} to {user.display_name} in #{message.channel.name}",
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to send held item ping for {pokemon_name} to {user.display_name} in #{message.channel.name}: {e}",
            )


# ─────────────────────────────
#  💎 Held Item Message
# ─────────────────────────────
def held_item_message(pokemon_name: str) -> str | None:
    """
    Generate a compact message for a Pokemon with held items.
    """
    held_item_phrase = f"{Emojis.item_hold} This Pokémon is holding an item!"

    items_for_pokemon = [
        item
        for item, data in HELD_ITEMS_DICT.items()
        if pokemon_name.lower() in data["pokemon"]
    ]
    proper_pokemon_name = pokemon_name.title()

    if not items_for_pokemon:
        return held_item_phrase  # No known held items for this Pokémon

    items_to_show = []
    for item in items_for_pokemon:
        items_to_show.append(f"**__{pretty_item_name(item)}__**")

    if not items_to_show:
        return None

    if len(items_to_show) == 1:
        return f"{held_item_phrase} (Special Item Chance: {items_to_show[0]})"
    else:
        items_str = " or ".join(items_to_show)
        return f"{held_item_phrase} (Special Item Chance: {items_str})"
