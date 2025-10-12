import re

import discord

from config.aesthetic import Emojis
from config.fish_rarity import FISH_RARITY
from config.rarity import rarity_meta
from utils.cache.cache_list import utility_cache
from utils.logs.debug_logs import debug_log, debug_message_content, enable_debug
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

# enable_debug(f"{__name__}.fish_rarity_embed")
# enable_debug(f"{__name__}.parse_pokemeow_fishing_spawn")
# ────────────────────────────────────────────
#   Constants and Regex Patterns
# ────────────────────────────────────────────
FISHING_COLOR = 0x87CEFA  # sky blue
NAME_PATTERN = re.compile(r"\*\*(?:(Shiny|Golden)\s+)?([A-Za-z_]+)\*\*", re.IGNORECASE)

WILD_SPAWN_PATTERN = re.compile(
    r"\*\*(?P<trainer>.+?)\*\*\s+fished a wild\s+"
    r"(?:<:[^>]+>)*\s*"
    r"(?:(?P<form>Shiny|Golden)\s+)?"
    r"(?:<:[^>]+>)*\s*"
    r"\*\*(?P<pokemon>[A-Za-z_]+)\*\*!",
    re.IGNORECASE,
)


# ────────────────────────────────────────────
#   Function: parse_pokemeow_fishing_spawn
# ────────────────────────────────────────────
def parse_pokemeow_fishing_spawn(message: discord.Message):
    debug_log("Starting fishing spawn parse")

    if not message.embeds:
        debug_log("No embeds found, returning None")
        return None

    embed = message.embeds[0]
    debug_log(f"Embed color: {embed.color} (expected: {FISHING_COLOR})")

    if not embed.color or embed.color.value != FISHING_COLOR:
        debug_log("Color mismatch, not a fishing embed")
        return None

    debug_log("Fishing color matched, proceeding with parse")

    trainer_id = None
    trainer_name = None
    if message.reference and getattr(message.reference, "resolved", None):
        resolved_author = getattr(message.reference.resolved, "author", None)
        trainer_id = resolved_author.id if resolved_author else None
        debug_log(f"Found trainer_id from reference: {trainer_id}")

    if not trainer_id and embed.description:
        name_match = re.search(r"\*\*(.+?)\*\*", embed.description)
        if name_match:
            trainer_name = name_match.group(1)
            debug_log(f"Extracted trainer_name from description: {trainer_name}")

    if not trainer_id and not trainer_name:
        debug_log("No trainer information found, returning None")
        return None

    pokemon_name = None
    form = None
    rarity = None
    valid_fish = False

    if embed.description:
        debug_log(f"Analyzing embed description: {embed.description!r}")

        for match in NAME_PATTERN.finditer(embed.description):
            candidate_form_raw = match.group(1)
            candidate_name = match.group(2).lower()
            candidate_form = candidate_form_raw.lower() if candidate_form_raw else None

            debug_log(
                f"Found name pattern - form: {candidate_form}, name: {candidate_name}"
            )

            for r, pokes in FISH_RARITY.items():
                if candidate_name in pokes:
                    pokemon_name = candidate_name
                    form = candidate_form
                    rarity = r

                    # 🌸 Override rarity for special forms
                    if candidate_form == "shiny":
                        rarity = "shiny"
                        debug_log(
                            "Overriding rarity to 'shiny' due to form", highlight=True
                        )
                    elif candidate_form == "golden":
                        rarity = "golden"
                        debug_log(
                            "Overriding rarity to 'golden' due to form", highlight=True
                        )

                    valid_fish = True
                    debug_log(
                        f"Valid fish found: {pokemon_name} ({form}) - {rarity}",
                        highlight=True,
                    )
                    break
            if valid_fish:
                break

    if not valid_fish:
        debug_log("No valid fish found in embed")
        return None

    result = {
        "type": "fishing",
        "pokemon": pokemon_name,
        "form": form,
        "rarity": rarity,
        "valid_fish": valid_fish,
        "user_id": trainer_id,
        "trainer_name": trainer_name,
        "raw_footer": embed.footer.text if embed.footer else "",
    }

    debug_log(f"Parse successful: {result}", highlight=True)
    return result


# ────────────────────────────────────────────
#   Function: fish_rarity_embed
# ────────────────────────────────────────────
async def fish_rarity_embed(
    bot, before_message: discord.Message, message: discord.Message
):
    debug_log("Starting fish rarity embed processing")
    debug_log(f"Utility cache: {utility_cache}")
    debug_message_content(message, force=False)

    spawn_info = parse_pokemeow_fishing_spawn(message)
    if not spawn_info:
        debug_log("No spawn info returned, exiting")
        return

    spawn_info_user_id = spawn_info["user_id"]
    trainer_name = spawn_info["trainer_name"]
    pokemon = spawn_info["pokemon"]
    form = spawn_info["form"]
    rarity = spawn_info["rarity"]
    valid_fish = spawn_info["valid_fish"]
    raw_footer = spawn_info["raw_footer"]

    user = await get_pokemeow_reply_member(before_message)
    user_id = user.id if user else spawn_info_user_id
    debug_log(f"Processing for user_id: {user_id}, trainer: {trainer_name}")

    utility_settings = utility_cache.get(user_id, {})

    if not utility_settings:
        debug_log("No utility settings found in cache")
        return

    debug_log(f"Utility settings: {utility_settings}")

    user = bot.get_user(user_id)
    if not user:
        debug_log("Could not fetch user object from bot")
        return

    fish_rarity_setting = (utility_settings.get("fish_rarity") or "off").lower()
    debug_log(f"Fish rarity setting: {fish_rarity_setting}")

    if fish_rarity_setting == "off":
        debug_log("Fish rarity setting is OFF, not sending embed")
        return

    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    display_fish_name = f"{rarity_emoji} {pokemon.title()}"
    embed_color = rarity_meta.get(rarity, {}).get("color", 0xFFFFFF)

    debug_log(f"Creating embed - name: {display_fish_name}, color: {embed_color}")

    desc = f"{Emojis.fish_embed} {user.display_name} found a {display_fish_name}!"
    embed = discord.Embed(description=desc, color=embed_color)

    debug_log("Sending fish rarity embed", highlight=True)
    await message.channel.send(embed=embed)

    pretty_log(
        tag="info",
        message=f"Sent fish rarity embed for {user.mention} ({pokemon}, {form}, {rarity})",
    )

    debug_log("Fish rarity embed sent successfully", highlight=True)
