import re

import discord

from config.aesthetic import *
from config.fairy_tale_constants import FAIRY_TAIL__TEXT_CHANNELS, FAIRY_TAIL_SERVER_ID
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

#🌺🧸────────────────────────────────────────────🌺🧸
#       GOLDEN_STONE_HELPERS
#🌺🧸────────────────────────────────────────────🌺🧸
def get_golden_stone_info(message: str) -> tuple[str, str] | None:
    """
    Extracts the emoji ID of a custom emoji with 'golden_' prefix
    and returns both its Discord CDN URL and the stone name
    (underscores removed, title case).

    Args:
        message (str): The Discord message content.

    Returns:
        tuple[str, str] | None: (emoji_url, stone_name) if found, otherwise None.
    """
    pattern = r"<:golden_([a-zA-Z0-9_]+):(\d+)>"
    match = re.search(pattern, message)
    if match:
        raw_name, emoji_id = match.groups()
        # Format the stone name: remove underscores, title case
        stone_name = raw_name.replace("_", " ").title()
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
        return emoji_url, stone_name
    return None


def get_mega_chamber(message: str) -> str | None:
    """
    Extracts the Mega Chamber challenge name (inside **bold**) from a Discord message.

    Args:
        message (str): The Discord message content.

    Returns:
        str | None: The challenge name (e.g. 'Mega Ampharos') if found, otherwise None.
    """
    # Look for bolded text after 'completed the' phrase
    pattern = r"completed the .*?\*\*(.*?)\*\*"
    match = re.search(pattern, message)
    if match:
        return match.group(1)
    return None

#🌺🧸────────────────────────────────────────────🌺🧸
#       GOLDEN_STONE_LISTENER
#🌺🧸────────────────────────────────────────────🌺🧸
async def golden_stone_listener(message: discord.Message):
    if message.guild.id != FAIRY_TAIL_SERVER_ID:  # fixed typo
        return

    result = get_golden_stone_info(message.content)
    if not result:
        return
    emoji_url, stone_name = result

    challenge_name = get_mega_chamber(message.content)
    if not challenge_name:
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        pretty_log(
            "info",
            f"Could not find member from PokéMeow reply. Message ID: {message.id}",
        )
        return

    rarespawn_channel = message.guild.get_channel(FAIRY_TAIL__TEXT_CHANNELS.rarespawn)
    content = (
        f"{member.mention} has stumbled across a Golden Team in **{challenge_name} Chamber**!"
    )
    embed = discord.Embed(
        title=stone_name,
        url=message.jump_url,
        color=discord.Color.gold(),
    )
    embed.set_image(url=emoji_url)
    await rarespawn_channel.send(content=content, embed=embed)
