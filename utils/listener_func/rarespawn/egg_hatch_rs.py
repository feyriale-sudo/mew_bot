import re

import discord

from config.rarity import *
from config.settings import Channels, Roles, users, MAIN_SERVER_ID
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

from .catch_and_fish import build_rare_spawn_embed

RARE_EGG_EXCLUSIVES = [
    "chingling",
    "mimejr",
    "happiny",
    "chatot",
    "munchlax",
    "riolu",
    "audino",
    "zorua",
    "emolga",
    "ferroseed",
    "golett",
    "pawniard",
    "pancham",
    "spritzee",
    "swirlix",
    "noibat",
    "crabrawler",
    "rockruff",
    "type-null",
    "yamper",
    "nickit",
]
SUPER_RARE_EGG_EXCLUSIVE = ["carbink", "mimikyu"]

REAL_RS_CHANNEL_ID = Channels.rare_spawn
TEST_RS_CHANNEL_ID = 1128425613447929859
valid_user_ids = [
    users.skaia,
    users.night,
]
processed_egg_hatches = set()
# ❀─────────────────────────────────────────❀
#      💖  Egg Hatch Listener
# ❀─────────────────────────────────────────❀
async def egg_rarespawn_handler(bot:discord.Client, message: discord.Message):
    """
    Handles egg hatch messages from PokéMeow to identify rare spawns.
    """
    embed = message.embeds[0] if message.embeds else None
    content = message.content if message.content else None
    if not embed and not content:
        return

    # Color
    embed_color = embed.color.value if embed else None

    # Extract Pokémon name from message content
    pokemon_name = None
    if content:
        # Pattern: "just hatched a <:447:...> **Riolu**!"
        hatch_match = re.search(r"just hatched a.*?\*\*([^*]+)\*\*", content)
        if hatch_match:
            pokemon_name = hatch_match.group(1).strip()
            pretty_log("debug", f"Egg hatch detected: {pokemon_name}")

    if not pokemon_name:
        return

    # Check if this is a rare/exclusive Pokémon
    is_rare_color = embed_color in RARE_SPAWN_COLORS.values() if embed_color else False
    is_egg_exclusive = pokemon_name.lower() in RARE_EGG_EXCLUSIVES or pokemon_name.lower() in SUPER_RARE_EGG_EXCLUSIVE

    if not (is_rare_color or is_egg_exclusive):
        pretty_log("debug", f"Skipping {pokemon_name} - not rare or egg exclusive")
        return

    # Extract user who hatched the egg
    user_member = await get_pokemeow_reply_member(message)
    if not user_member:
        return
    if user_member.id not in valid_user_ids:
        return

    skaia_server = bot.get_guild(MAIN_SERVER_ID)

    if message.id in processed_egg_hatches:
        return
    processed_egg_hatches.add(message.id)

    image_url = embed.image.url if embed.image else None
    raw_pokemon_name = pokemon_name.lower()
    display_pokemon_name = ""
    rarity = "rare"
    if "shiny" in pokemon_name.lower():
        rarity = "shiny"
        # Keep raw_pokemon_name as "shiny mew" for cache lookup
        pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
    elif "golden" in pokemon_name.lower():
        rarity = "golden"
        # Keep raw_pokemon_name as "golden mew" for cache lookup
        pokemon_name = pokemon_name.replace("Golden ", "")  # Clean for display
    elif pokemon_name.lower() in SUPER_RARE_EGG_EXCLUSIVE:
        rarity = "superrare"

    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    display_pokemon_name = pokemon_name.title()
    context = "hatched"

    content, embed = build_rare_spawn_embed(
        message=message,
        member=user_member,
        pokemon_name=display_pokemon_name,
        context=context,
        image_url=image_url,
        color=embed_color,
        raw_pokemon_name=raw_pokemon_name,
        rarity_emoji=rarity_emoji
    )

    rarespawn_channel = skaia_server.get_channel(
        REAL_RS_CHANNEL_ID
    )  # Use bot.get_channel
    if rarespawn_channel:
        await rarespawn_channel.send(content=content, embed=embed)
        pretty_log(
            "info",
            f"Egg rare spawn detected: {pokemon_name}  for {user_member.display_name}",
        )
