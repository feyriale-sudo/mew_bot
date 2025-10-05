import discord
from discord.ext import commands


# 🌸───────────────────────────────────────────────
# 🐾 Fetch Message from Link Helper
# Returns: (success: bool, message: discord.Message | None, error_msg: str | None)
# 🌸───────────────────────────────────────────────
async def fetch_message_from_link(bot: commands.Bot, message_link: str):
    """
    Given a Discord message link, fetches the message object.
    Returns a tuple: (success, message, error_msg)
    """

    # Step 1: Validate input
    if not message_link or "/" not in message_link:
        return False, None, "❌ Oopsie! That doesn’t look like a valid message link. 🐾"

    # Step 2: Extract guild, channel, and message IDs
    try:
        parts = message_link.strip().split("/")
        guild_id = int(parts[4])
        channel_id = int(parts[5])
        message_id = int(parts[6])
    except (IndexError, ValueError):
        return (
            False,
            None,
            "❌ Oopsie! That message link looks wrong. Please double-check! 🐾",
        )

    # Step 3: Fetch the message lovingly
    try:
        channel = await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        return True, message, None
    except discord.NotFound:
        return False, None, "❌ Message not found. Maybe it disappeared? 🕵️‍♂️"
    except discord.Forbidden:
        return False, None, "❌ I don’t have permission to peek at that message! 🙅‍♀️"
    except Exception as e:
        return False, None, f"❌ Unexpected error fetching message: {e} 😿"
