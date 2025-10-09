import re

import discord

from config.aesthetic import Emojis
from config.rarity import *
from config.settings import Channels, Roles
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

from .catch_and_fish import build_rare_spawn_embed


# ❀─────────────────────────────────────────❀
#      💖  Swap Listener
# ❀─────────────────────────────────────────❀
async def swap_rarespawn_handler(bot, message: discord.Message):
    """
    Handles swap messages from PokéMeow to identify rare spawns.
    """
    embed = message.embeds[0] if message.embeds else None
    content = message.content if message.content else None
    if not embed and not content:
        return

    # Color
    embed_color = embed.color.value if embed and embed.color else None

    # Check if it's a rare spawn color
    is_rare_color = embed_color in RARE_SPAWN_COLORS.values() if embed_color else False

    if not is_rare_color:
        return

    # Extract Pokémon name from embed description or message content
    pokemon_name = None

    # Try to extract from embed description first
    if embed and embed.description:
        # Pattern: "received a <:Common:...> <:273:...> **Seedot** from a swap!"
        swap_match = re.search(
            r"received a.*?\*\*([^*]+)\*\*.*?from a swap", embed.description
        )
        if swap_match:
            pokemon_name = swap_match.group(1).strip()
            pretty_log("debug", f"Swap detected (embed): {pokemon_name}")

    # Fallback to message content if embed extraction failed
    if not pokemon_name and content:
        # Pattern: "khy.09 received: <:Common:...> <:273:...> **Seedot**"
        content_match = re.search(r"received:.*?\*\*([^*]+)\*\*", content)
        if content_match:
            pokemon_name = content_match.group(1).strip()
            pretty_log("debug", f"Swap detected (content): {pokemon_name}")

    if not pokemon_name:
        pretty_log("debug", "Could not extract Pokémon name from swap message")
        return

    # Extract user who performed the swap
    user_member = await get_pokemeow_reply_member(message)
    if not user_member:
        return

    # Determine rarity and prepare names
    rarity = "unknown"
    original_pokemon_name = pokemon_name
    raw_pokemon_name = pokemon_name.lower()

    # Check for special variants in the name
    if "shiny" in pokemon_name.lower():
        rarity = "shiny"
        raw_pokemon_name = pokemon_name.lower()  # Keep "shiny seedot" for cache
        pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
    elif "golden" in pokemon_name.lower():
        rarity = "golden"
        raw_pokemon_name = pokemon_name.lower()  # Keep "golden seedot" for cache
        pokemon_name = pokemon_name.replace("Golden ", "")  # Clean for display
    elif is_rare_color:
        # Determine rarity based on color
        for rarity_name, rarity_data in rarity_meta.items():
            if rarity_data.get("color") == embed_color:
                rarity = rarity_name
                break

    # Build display name with emoji
    if rarity in rarity_meta:
        display_pokemon_name = f"{rarity_meta[rarity]['emoji']} {pokemon_name.title()}"
    else:
        display_pokemon_name = pokemon_name.title()

    # Get image URL from embed
    image_url = embed.image.url if embed and embed.image else None

    # Use "caught" context for swaps (reusing existing dict entry)
    context = "caught"

    # Build the rare spawn embed
    content_msg, embed_msg = build_rare_spawn_embed(
        message=message,
        member=user_member,
        pokemon_name=display_pokemon_name,
        context=context,
        image_url=image_url,
        color=embed_color or rarity_meta.get(rarity, {}).get("color", 0x000000),
        raw_pokemon_name=raw_pokemon_name,
    )

    # Send to rare spawn channel
    rarespawn_channel = bot.get_channel(Channels.rare_spawn)
    if rarespawn_channel:
        await rarespawn_channel.send(content=content_msg, embed=embed_msg)
        pretty_log(
            "info",
            f"Swap rare spawn detected: {original_pokemon_name} received by {user_member.display_name}",
        )
