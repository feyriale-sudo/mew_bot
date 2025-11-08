from datetime import datetime

import discord

from config.fairy_tale_constants import FAIRY_TAIL__TEXT_CHANNELS
from config.settings import MAIN_SERVER_ID
from utils.logs.pretty_log import pretty_log


# 🐾──────────────────────────────────────────────
#       Daily Pokemeow Reminder Ping
# 🐾──────────────────────────────────────────────
async def daily_pokemeow_reminder(bot):
    """Send a daily reminder to the Pokemeow channel."""
    try:
        main_guild: discord.Guild = bot.get_guild(MAIN_SERVER_ID)
        if not main_guild:
            pretty_log(
                tag="error",
                message="Main guild not found for daily Pokemeow reminder.",
                bot=bot,
            )
            return

        amnesia_channel = main_guild.get_channel(FAIRY_TAIL__TEXT_CHANNELS.amnesia)
        if not amnesia_channel:
            pretty_log(
                tag="error",
                message="Amnesia channel not found for daily Pokemeow reminder.",
                bot=bot,
            )
            return

        embed = discord.Embed(
            title="Dαilies ♡",
            description="✓ ;cl - ;lot buy x",
            color=13725576,
            timestamp=datetime.now(),
        )
        image_url = "https://images-ext-1.discordapp.net/external/n-eU2SGmQxLZ3IcfNbcLsqPaQyMMGKIrYtIyeP6fnfI/https/images-ext-1.discordapp.net/external/NNVQp5dV3VMtKVwmp9iTQKHPddsndIeun1RS4gsvuA4/https/play.pokemonshowdown.com/sprites/ani-shiny/lopunny-mega.gif"
        embed.set_image(url=image_url)
        await amnesia_channel.send(embed=embed)
        pretty_log(
            tag="background_task",
            message="Sent daily Pokemeow reminder in Amnesia channel.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error in daily Pokemeow reminder task: {e}",
            bot=bot,
        )
