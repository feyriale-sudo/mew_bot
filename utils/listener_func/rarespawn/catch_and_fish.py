import re

import discord

from config.aesthetic import Emojis
from config.rarity import *
from config.settings import Channels, Roles
from utils.cache.cache_list import market_value_cache
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member




# ❀─────────────────────────────────────────❀
#      💖  Catch and Fish Listener
# ❀─────────────────────────────────────────❀
async def catch_and_fish_message_rare_spawn_handler(
    bot, before: discord.Message, after: discord.Message
):
    """
    Handles catch and fish messages from PokéMeow to identify rare spawns.
    """
    embed = after.embeds[0]
    if not embed:
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""

    # Check if it's NOT a rare spawn color, or if it's fishing but doesn't contain rarity triggers
    if embed_color not in RARE_SPAWN_COLORS.values() or (
        embed_color == FISHING_COLOR
        and not any(trigger in embed_description for trigger in FISHING_RARITY_TRIGGERS)
    ):
        pretty_log("debug", f"Skipping - not rare color or fishing without triggers")
        return

    # Get Member
    member = await get_pokemeow_reply_member(before)
    if not member:
        return
    spawn_type = "pokemon" if embed_color != FISHING_COLOR else "fish"

    pokemon_name = ""
    # Process rare spawn caught
    if "You caught" in embed_description:
        context = "caught"
        # Extract Pokemon name from "You caught a ... **PokemonName** with a ..."
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed_description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()
    elif "broke out" in embed_description:
        context = "broke_out"
        # Extract Pokemon name from similar pattern when Pokemon breaks out
        broke_match = re.search(r"\*\*([^*]+)\*\*.*?broke out", embed_description)
        if broke_match:
            pokemon_name = broke_match.group(1).strip()
            pretty_log(
                "debug", f"Extracted Pokemon name from 'broke out': {pokemon_name}"
            )
        else:
            pretty_log(
                "debug", f"Could not match 'broke out' pattern in: {embed_description}"
            )
    elif "ran away" in embed_description:
        context = "ran_away"
        # Extract Pokemon name from similar pattern when Pokemon runs away
        ran_match = re.search(r"\*\*([^*]+)\*\*.*?ran away", embed_description)
        if ran_match:
            pokemon_name = ran_match.group(1).strip()

    if not pokemon_name:
        pretty_log("debug", f"Could not extract Pokemon name from: {embed_description}")
        return

    pretty_log(
        "info",
        f"Rare spawn detected: {pokemon_name} ({context}) for {member.display_name}",
    )

    rarity = ""
    raw_pokemon_name = pokemon_name.lower()  # Store original for cache lookup

    display_pokemon_name = ""
    if spawn_type == "fish":
        if "shiny" in pokemon_name.lower():
            rarity = "shiny"
            # Keep raw_pokemon_name as "shiny mew" for cache lookup
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
        elif "golden" in pokemon_name.lower():
            rarity = "golden"
            # Keep raw_pokemon_name as "golden mew" for cache lookup
            pokemon_name = pokemon_name.replace("Golden ", "")  # Clean for display
        elif "kyogre" in pokemon_name.lower() or "suicune" in pokemon_name.lower():
            rarity = "legendary"

    elif spawn_type == "pokemon":
        if embed_color == rarity_meta["legendary"]["color"]:
            rarity = "legendary"
        elif embed_color == rarity_meta["shiny"]["color"]:
            rarity = "shiny"
            raw_pokemon_name = f"shiny {pokemon_name.lower()}"  # Shiny spawns need "shiny" prefix for cache
        elif embed_color != rarity_meta["event_exclusive"]["color"]:
            # Extract rarity from embed footer
            if embed.footer and embed.footer.text:
                footer_text = embed.footer.text
                # Look for "Rarity: RarityName" pattern
                rarity_match = re.search(r"Rarity:\s*(\w+)", footer_text)
                if rarity_match:
                    rarity = rarity_match.group(1).lower()
                    if rarity == "super rare":
                        rarity = "superrare"
                    pretty_log("debug", f"Extracted rarity: {rarity}")
                else:
                    pretty_log(
                        "debug", f"Could not extract rarity from footer: {footer_text}"
                    )

    display_pokemon_name = f"{rarity_meta[rarity]['emoji']} {pokemon_name.title()}"
    image_url = embed.image.url if embed.image else None

    content, embed = build_rare_spawn_embed(
        message=after,
        member=member,
        pokemon_name=display_pokemon_name,
        context=context,
        image_url=image_url,
        color=embed_color,
        raw_pokemon_name=raw_pokemon_name,
    )

    rarespawn_channel = member.guild.get_channel(Channels.rare_spawn)
    if rarespawn_channel:
        await rarespawn_channel.send(content=content, embed=embed)
        pretty_log(
            "info",
            f"Posted rare spawn of {pokemon_name} ({context}) for {member.display_name} in #{rarespawn_channel.name}",
        )

# 💖─────────────────────────────────────────💖
#     Build Rare Spawn Embed
# 💖─────────────────────────────────────────💖
def build_rare_spawn_embed(
    message: discord.Message,
    member: discord.Member,
    pokemon_name: str,
    raw_pokemon_name: str,
    context: str,
    image_url: str,
    color,
):
    content = f"Attention all <@&{Roles.rare_spawn}> — {member.mention} has found a [{pokemon_name}]({message.jump_url})!"
    footer_text = CONTEXT_MAP[context]["footer"]
    catch_status = CONTEXT_MAP[context]["emoji"]

    # Look up market value using the clean pokemon name (before adding rarity emoji)
    clean_pokemon_name = raw_pokemon_name.lower()
    value_data = market_value_cache.get(clean_pokemon_name)
    lowest_market = value_data["lowest_market"] if value_data else None
    display_lowest_market = ""
    as_of = ""
    if lowest_market:
        display_lowest_market = f" {Emojis.PokeCoin} {lowest_market:,}"
        as_of = value_data.get("listing_seen", "")
    else:
        display_lowest_market = f" {Emojis.PokeCoin} ?"
        as_of = "?"

    embed = discord.Embed(color=color)
    embed.add_field(
        name=f"Value as of {as_of}", value=f"{display_lowest_market}", inline=False
    )
    embed.add_field(name=f"Catch Status", value=f"{catch_status}", inline=False)
    embed.set_footer(
        text=footer_text, icon_url=message.guild.icon.url if message.guild else None
    )
    embed.color = color
    embed.set_image(url=image_url)

    return content, embed
