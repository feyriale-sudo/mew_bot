import re

import discord

from config.aesthetic import Emojis
from config.rarity import *
from config.settings import Channels, Roles
from utils.cache.cache_list import market_value_cache
from utils.logs.debug_logs import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

enable_debug(f"{__name__}.catch_and_fish_message_rare_spawn_handler")
enable_debug(f"{__name__}.build_rare_spawn_embed")

HALLOWEEN_COLOR = 0xFFA500  # orange

REAL_RS_CHANNEL_ID = Channels.rare_spawn
TEST_RS_CHANNEL_ID = 1128425613447929859
# ❀─────────────────────────────────────────❀
#      💖  Catch and Fish Listener
# ❀─────────────────────────────────────────❀
async def catch_and_fish_message_rare_spawn_handler(
    bot, before: discord.Message, after: discord.Message
):
    """
    Handles catch and fish messages from PokéMeow to identify rare spawns.
    """
    debug_log("Entered catch_and_fish_message_rare_spawn_handler")
    embed = after.embeds[0]
    if not embed:
        debug_log("No embed found in message.", highlight=True)
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""
    debug_log(f"Embed color: {embed_color}, description: {embed_description!r}")

    # Get Ball Used
    ball_used = None
    ball_emoji = None
    ball_match = re.search(
        r"<:([a-zA-Z0-9_]+):\d+>\s*([A-Za-z]+ball)", embed_description, re.IGNORECASE
    )
    if ball_match:
        ball_used = ball_match.group(2).lower()  # "pokeball"
        ball_emoji_name = ball_match.group(1)    # "pokeball"
        ball_emoji = getattr(Emojis, ball_emoji_name, None)
        debug_log(f"Ball used: {ball_used}, Ball emoji: {ball_emoji}")
    else:
        debug_log("No ball used found in description.")

    # Check if it's NOT a rare spawn color, or if it's fishing but doesn't contain rarity triggers
    if embed_color not in RARE_SPAWN_COLORS.values() or embed_color == HALLOWEEN_COLOR or (
        embed_color == FISHING_COLOR
        and not any(trigger in embed_description for trigger in FISHING_RARITY_TRIGGERS)
    ):
        debug_log(
            "Embed color not in rare spawn colors or missing fishing rarity triggers.",
            highlight=True,
        )
        return

    # Get Member
    member = await get_pokemeow_reply_member(before)
    if not member:
        debug_log("Could not resolve member from message.", highlight=True)
        return
    spawn_type = "pokemon" if embed_color != FISHING_COLOR else "fish"
    debug_log(f"Spawn type determined: {spawn_type}")

    # Get Ball Used
    ball_used = None
    ball_emoji = None
    ball_match = re.search(
        r"<:([a-zA-Z0-9_]+):\d+>\s*([A-Za-z]+ball)", embed_description, re.IGNORECASE
    )
    if ball_match:
        ball_used = ball_match.group(2).lower()  # "pokeball"
        ball_emoji_name = ball_match.group(1)  # "pokeball"
        ball_emoji = getattr(Emojis, ball_emoji_name, None)
        debug_log(f"Ball used: {ball_used}, Ball emoji: {ball_emoji}")
    else:
        debug_log("No ball used found in description.")

    # Determine context and extract Pokemon name
    pokemon_name = ""
    # Process rare spawn caught
    if "You caught" in embed_description:
        context = "caught"
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed_description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()
            debug_log(f"Extracted Pokemon name (caught): {pokemon_name}")
        else:
            debug_log(
                "Could not extract Pokemon name from caught pattern.", highlight=True
            )
    elif "broke out" in embed_description:
        context = "broke_out"
        broke_match = re.search(r"\*\*([^*]+)\*\*.*?broke out", embed_description)
        if broke_match:
            pokemon_name = broke_match.group(1).strip()
            debug_log(f"Extracted Pokemon name from 'broke out': {pokemon_name}")
        else:
            debug_log(
                f"Could not match 'broke out' pattern in: {embed_description}",
                highlight=True,
            )
    elif "ran away" in embed_description:
        context = "ran_away"
        ran_match = re.search(r"\*\*([^*]+)\*\*.*?ran away", embed_description)
        if ran_match:
            pokemon_name = ran_match.group(1).strip()
            debug_log(f"Extracted Pokemon name from 'ran away': {pokemon_name}")
        else:
            debug_log(
                "Could not extract Pokemon name from ran away pattern.", highlight=True
            )

    if not pokemon_name:
        debug_log(
            f"Could not extract Pokemon name from: {embed_description}", highlight=True
        )
        return

    debug_log(
        f"Rare spawn detected: {pokemon_name} ({context}) for {member.display_name}",
        highlight=True,
    )

    rarity = ""
    raw_pokemon_name = pokemon_name.lower()  # Store original for cache lookup
    rarity_emoji = ""
    display_pokemon_name = None
    if spawn_type == "fish":
        if "shiny" in pokemon_name.lower():
            rarity = "shiny"
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
            debug_log("Detected shiny fish spawn.")
        elif "golden" in pokemon_name.lower():
            rarity = "golden"
            pokemon_name = pokemon_name.replace("Golden ", "")  # Clean for display
            debug_log("Detected golden fish spawn.")
        elif "kyogre" in pokemon_name.lower() or "suicune" in pokemon_name.lower():
            rarity = "legendary"
            debug_log("Detected legendary fish spawn.")
    #
    elif spawn_type == "pokemon":
        if embed_color == rarity_meta["legendary"]["color"]:
            rarity = "legendary"
            debug_log("Detected legendary pokemon spawn.")
        elif embed_color == rarity_meta["shiny"]["color"]:
            rarity = "shiny"
            debug_log("Detected shiny pokemon spawn.")
        elif embed_color == rarity_meta["event_exclusive"]["color"] or embed_color == rarity_meta["halloween"]["color"]:
            rarity = "event_exclusive"
            debug_log("Detected event exclusive or halloween pokemon spawn.")
            # Extract rarity from embed footer
            if embed.footer and embed.footer.text:
                footer_text = embed.footer.text
                rarity_match = re.search(r"Rarity:\s*([A-Za-z]+)", footer_text)
                if rarity_match:
                    rarity = rarity_match.group(1).strip().lower().replace(" ", "")
                    debug_log(f"Extracted rarity: {rarity}")
                else:
                    debug_log(
                        f"Could not extract rarity from footer: {footer_text}",
                        highlight=True,
                    )
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    display_pokemon_name = pokemon_name.title()
    image_url = embed.image.url if embed.image else None

    debug_log(f"Building rare spawn embed for {display_pokemon_name} ({rarity})")
    content, embed = build_rare_spawn_embed(
        message=after,
        member=member,
        pokemon_name=display_pokemon_name,
        context=context,
        image_url=image_url,
        color=embed_color,
        raw_pokemon_name=raw_pokemon_name,
        rarity_emoji=rarity_emoji,
        ball_emoji=ball_emoji,
    )

    rarespawn_channel = member.guild.get_channel(REAL_RS_CHANNEL_ID)
    if rarespawn_channel:
        await rarespawn_channel.send(content=content, embed=embed)
        debug_log(
            f"Posted rare spawn of {pokemon_name} ({context}) for {member.display_name} in #{rarespawn_channel.name}",
            highlight=True,
        )


# 💖─────────────────────────────────────────💖
#     Build Rare Spawn Embed
# 💖─────────────────────────────────────────💖
def build_rare_spawn_embed(
    message: discord.Message,
    member: discord.Member,
    pokemon_name: str,
    rarity_emoji: str,
    raw_pokemon_name: str,
    context: str,
    image_url: str,
    color,
    ball_emoji: str = None,
):
    debug_log(f"Building embed for {pokemon_name} ({context})")
    content = f"Attention all <@&{Roles.rare_spawn}> — {member.mention} has found a {rarity_emoji} [{pokemon_name}]({message.jump_url})!"
    footer_text = CONTEXT_MAP[context]["footer"]
    catch_status = CONTEXT_MAP[context]["emoji"]

    pretty_log("debug", f"Ball emoji: {ball_emoji}")
    if ball_emoji:
        catch_status += f" {ball_emoji}"
    if context == "hatched":
        content = f"Attention all <@&{Roles.rare_spawn}> — {member.mention} just hatched a {rarity_emoji} [{pokemon_name}]({message.jump_url})!"
        catch_status = f"{Emojis.egg} {catch_status}"

    # Look up market value using the clean pokemon name (before adding rarity emoji)
    clean_pokemon_name = raw_pokemon_name.lower()
    value_data = market_value_cache.get(clean_pokemon_name)
    lowest_market = value_data["lowest_market"] if value_data else None
    display_lowest_market = ""
    as_of = ""
    if lowest_market:
        display_lowest_market = f" {Emojis.PokeCoin} {lowest_market:,}"
        as_of = value_data.get("listing_seen", "")
        debug_log(f"Market value found: {lowest_market} as of {as_of}")
    else:
        display_lowest_market = f" {Emojis.PokeCoin} ?"
        as_of = "?"
        debug_log("No market value found.")

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

    debug_log(f"Embed built for {pokemon_name} ({context})")
    return content, embed
