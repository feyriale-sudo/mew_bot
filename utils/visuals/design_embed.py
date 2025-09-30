import random
from datetime import datetime

import discord

from utils.pokemeow.pokemon_gif import get_pokemon_gif


def format_bulletin_desc(*args, key_style_override: str = None) -> str:
    """
    Flexible bulletin formatter.
    - By default, keys are bold.
    - If key_style_override is provided, all keys use that style.
    - Skips any key/value pair where the value is None or empty string.
    """

    def apply_style(text: str, style: str) -> str:
        style = style.lower()
        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"*{text}*"
        elif style == "underline":
            return f"__{text}__"
        elif style == "strikethrough":
            return f"~~{text}~~"
        elif style == "spoiler":
            return f"||{text}||"
        elif style == "inline_code":
            return f"`{text}`"
        elif style == "code":
            return f"```\n{text}\n```"
        elif style == "bold_upper":
            return f"**{text.upper()}**"
        else:
            return f"**{text}**"  # default bold

    key_style = key_style_override if key_style_override else "bold"

    lines = []
    i = 0
    while i < len(args):
        key = args[i]
        value = args[i + 1] if i + 1 < len(args) else None

        # 🔹 Skip if value is None or empty string
        if value is None or (isinstance(value, str) and value.strip() == ""):
            i += 2
            continue

        formatted_key = apply_style(f"{key}:", key_style)
        lines.append(f"- {formatted_key} {value}")

        i += 2

    return "\n".join(lines)


# 💖 Expanded Mew palette
MEW_PALETTE = {
    "soft_pink": ["#FFD6E8", "#FFCCE0", "#FFB6D9", "#FF99CC", "#FF85C1", "#FFB3DE"],
    "light_pink": ["#FFCCE6", "#FFB3D9", "#FFA6CC", "#FF99BF", "#FF8FCF", "#FF7FBF"],
    "pastel_magenta": [
        "#FF99E6",
        "#FF66CC",
        "#FF66B3",
        "#FF4DB8",
        "#FF3399",
        "#FF66FF",
    ],
    "pink_peach": ["#FFD1DC", "#FFB6C1", "#FF9BBF", "#FF80A5", "#FF66A3"],
    "bubblegum": ["#FFB3E6", "#FF99DD", "#FF80CC", "#FF66C2", "#FF4DAA"],
    "mauve_pink": ["#E6A6D9", "#D990C9", "#D17EBF", "#C06AB3", "#B459A6"],
}


# ── Core color functions ─────────────────────────────
def get_random_mew_shade(shade: str = None) -> discord.Colour:
    """Returns a random Mew-themed pastel color. If shade is None, pick randomly from all shades."""
    if not shade or shade not in MEW_PALETTE:
        shade = random.choice(list(MEW_PALETTE.keys()))
    color_ints = [int(c.lstrip("#"), 16) for c in MEW_PALETTE[shade]]
    return discord.Colour(random.choice(color_ints))


def get_random_mew_color() -> discord.Colour:
    """Returns any random Mew color (full palette)."""
    return get_random_mew_shade()


# ── Convenience shade helpers ─────────────────────────
get_random_soft_pink = lambda: get_random_mew_shade("soft_pink")
get_random_light_pink = lambda: get_random_mew_shade("light_pink")
get_random_pastel_magenta = lambda: get_random_mew_shade("pastel_magenta")
get_random_pink_peach = lambda: get_random_mew_shade("pink_peach")
get_random_bubblegum = lambda: get_random_mew_shade("bubblegum")
get_random_mauve_pink = lambda: get_random_mew_shade("mauve_pink")


# ── Embed helper ─────────────────────────────
async def design_embed(
    embed: discord.Embed,
    user: discord.User | discord.Member,
    thumbnail_url: str = None,
    image_url: str = None,
    footer_text: str = None,
    pokemon_name: str = None,
    color: discord.Colour | str = None,
) -> discord.Embed:
    """
    Sets the embed's author, thumbnail, image, footer, and optional color.
    - Author text = user's display name
    - Author icon = user's avatar
    - Thumbnail = thumbnail_url or user's avatar
    - Image = image_url if provided
    - Footer = footer_text or user ID
    - Color = Discord Color or Espeon shade string
    """
    avatar_url = user.display_avatar.url
    embed.set_author(name=user.display_name, icon_url=avatar_url)
    embed.timestamp = datetime.now()

    if pokemon_name:
        pokemon_gif = await get_pokemon_gif(pokemon_name)
        if pokemon_gif:
            thumbnail_url = pokemon_gif

    # Set thumbnail
    embed.set_thumbnail(url=thumbnail_url or avatar_url)

    # Set image if provided
    if image_url:
        embed.set_image(url=image_url)

    # Set footer
    embed.set_footer(
        text=footer_text or f"💫 User ID: {user.id}",
        icon_url=(
            getattr(user.guild.icon, "url", None) if hasattr(user, "guild") else None
        ),
    )

    # Set color
    if isinstance(color, str):
        embed.color = get_random_mew_shade(color)
    elif isinstance(color, discord.Colour):
        embed.color = color
    else:
        embed.color = 16744613

    return embed


import discord

ERROR_LOG_CHANNEL_ID = 1410202143570530375


async def pokemon_embed(
    embed: discord.Embed, pokemon_name: str, bot: discord.Client
) -> discord.Embed:
    """
    Inserts a Pokémon GIF in the embed thumbnail.
    Logs a warning to the botlog if the GIF is invalid or missing.
    """
    # Fetch the Pokémon GIF (assume it returns a URL string or None)
    pokemon_gif = await get_pokemon_gif(pokemon_name)

    if not pokemon_gif or not isinstance(pokemon_gif, str) or not pokemon_gif.strip():
        # Send warning to botlog channel
        botlog_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if botlog_channel:
            await botlog_channel.send(
                f"⚠️ Pokémon '{pokemon_name}' does not have a proper GIF for the thumbnail."
            )
        return embed  # still return the embed, just without thumbnail

    embed.set_thumbnail(url=pokemon_gif)
    return embed
