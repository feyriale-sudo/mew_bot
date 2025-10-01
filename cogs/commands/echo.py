# 🌸───────────────────────────────────────────────
#                  Echo Cog
# 🌸───────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Emojis
from utils.logs.pretty_log import pretty_log
from utils.visuals.pretty_defer import pretty_defer


class EchoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🌸───────────────────────────────────────────────
    #           Slash Command: /echo
    # 🌸───────────────────────────────────────────────
    @app_commands.command(
        name="echo",
        description="Send a message to a channel, with optional sparkles and tagging",
    )
    @app_commands.describe(
        channel="The channel where the message will be sent",
        message="The message you want to send",
        sparkle="Add sparkles around the message",
        member="Optional member to tag in the message",
    )
    async def echo(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
        sparkle: bool = False,
        member: discord.Member | None = None,
    ):
        loader = await pretty_defer(
            interaction=interaction,
            content=f"Sending message to {channel.mention}...",
            ephemeral=True,
        )

        SPARKLE_EMOJI = Emojis.Pink_Sparkles

        # 🌸 Construct message content
        if sparkle and member and channel.permissions_for(member).read_messages:
            content = f"## {SPARKLE_EMOJI} {member.mention} {message} {SPARKLE_EMOJI}"
        elif sparkle:
            content = f"## {SPARKLE_EMOJI} {message} {SPARKLE_EMOJI}"
        elif member and channel.permissions_for(member).read_messages:
            content = f"{member.mention} {message}"
        else:
            content = message

        # 🌸 Send the message
        await channel.send(content)
        await loader.success(content=f"Message sent to {channel.mention}")

        # 🌸 Pretty log
        log_msg = (
            f"{interaction.user} echoed a message to {channel.name} (sparkle={sparkle})"
        )
        if member:
            log_msg += f", tagged_member={member}"
        pretty_log("info", log_msg)


# 🌸───────────────────────────────────────────────
#                   Cog Setup
# 🌸───────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(EchoCog(bot))
