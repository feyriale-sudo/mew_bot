import re

import discord

from config.aesthetic import *
from config.fairy_tale_constants import (
    FAIRY_TAIL__TEXT_CHANNELS,
    FAIRY_TAIL_SERVER_ID,
    MEW_COLOR,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member


def get_npc_info(message: str) -> tuple[str, str] | None:
    """
    Extracts the emoji ID of a custom emoji (like chamber_...) and the NPC name
    from a line starting with '- Set ...' in a Discord message.

    Args:
        message (str): The Discord message content.

    Returns:
        tuple[str, str] | None: (emoji_url, npc_name) if found, otherwise None.
    """
    # Regex: look for "- Set <emoji> **Name**"
    pattern = r"- Set\s+<:([a-zA-Z0-9_]+):(\d+)>\s+\*\*(.*?)\*\*"
    match = re.search(pattern, message)
    if match:
        raw_name, emoji_id, npc_name = match.groups()
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
        return emoji_url, npc_name
    return None

#🌺🧸────────────────────────────────────────────🌺🧸
#       BATTLE_UNLOCK_LISTENER
#🌺🧸────────────────────────────────────────────🌺🧸
async def battle_unlock_listener(message: discord.Message):
    if message.guild.id != FAIRY_TAIL_SERVER_ID:  # fixed typo
        return

    result = get_npc_info(message.content)
    if not result:
        return
    emoji_url, npc_name = result

    member = await get_pokemeow_reply_member(message)
    if not member:
        pretty_log(
            "info",
            f"Could not find member from PokéMeow reply. Message ID: {message.id}",
        )
        return

    rarespawn_channel = message.guild.get_channel(FAIRY_TAIL__TEXT_CHANNELS.rarespawn)
    content = f"{member.mention} has unlocked an icon!"
    embed = discord.Embed(
        title=npc_name,
        url=message.jump_url,
        color=MEW_COLOR,
    )
    embed.set_image(url=emoji_url)
    await rarespawn_channel.send(content=content, embed=embed)
