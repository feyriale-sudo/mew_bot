import discord
from discord import app_commands
from discord.ext import commands

from config.rarity import *
from utils.listener_func.rarespawn.catch_and_fish import (
    catch_and_fish_message_rare_spawn_handler,
)
from typing import Literal


class FakeReference:
    def __init__(self, resolved):
        self.resolved = resolved


class FakeMessage:
    def __init__(self, guild, author, embeds, reference=None):
        self.guild = guild
        self.author = author
        self.embeds = embeds
        self.content = ""
        self.jump_url = ""
        self.channel = None
        self.reference = reference


class FakeMember:
    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.display_name = getattr(user, "display_name", user.name)
        self.mention = f"<@{user.id}>"
        self.guild = None


class TestRareSpawn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="test-rarespawn", description="Test rare spawn handler with custom values."
    )
    @app_commands.describe(
        context="The context of the rare spawn (caught, broke out, fled, hatched).",
        rarity="The rarity of the rare spawn.",
        color="The color category of the rare spawn.",
        ball_used="The type of Poké Ball used (if applicable).",
        pokemon="The name of the Pokémon.",
        image_url="Optional image URL for the embed.",
    )
    async def testrarespawn(
        self,
        interaction: discord.Interaction,
        context: Literal["caught", "broke out", "fled", "hatched"],
        rarity: Literal[
            "common", "uncommon", "rare", "superrare", "legendary", "shiny", "golden"
        ],
        color: Literal[
            "common",
            "uncommon",
            "rare",
            "superrare",
            "legendary",
            "shiny",
            "golden",
            "halloween",
            "fishing",
            "event_exclusive",
        ],
        ball_used: Literal[
            "pokeball",
            "greatball",
            "ultraball",
            "premierball",
            "masterball",
            "beastball",
        ],
        pokemon: str,
        image_url: str = "",
    ):
        # Build embed description and footer
        footer_text = None
        description = ""
        if context != "hatched":
            if rarity == "superrare":
                rarity = "super rare"
            footer_text = f"Rarity: {rarity.title()}"
            if context == "caught":
                description = (
                    f"You caught a **{pokemon.title()}** with a {ball_used.title()}!"
                )
            elif context == "broke out":
                description = (
                    f"**{pokemon.title()}** broke out of the {ball_used.title()}!"
                )
            elif context == "fled":
                description = f"**{pokemon.title()}** ran away"
        else:
            description = f"**{pokemon.title()}** hatched from an egg!"

        # Get color value from rarity_meta
        color_value = rarity_meta.get(color, {}).get("color", 0xA0D8F0)
        embed = discord.Embed(description=description, color=color_value)
        if footer_text:
            embed.set_footer(text=footer_text)
        if image_url:
            embed.set_image(url=image_url)

        # Simulate a reply reference for PokéMeow bot message
        fake_guild = interaction.guild
        # Use a real discord.Member if possible
        member = None
        if fake_guild:
            member = fake_guild.get_member(interaction.user.id)
        if not member and isinstance(interaction.user, discord.Member):
            member = interaction.user
        if not member:
            # Fallback: just use interaction.user, but handler may not recognize it
            member = FakeMember(interaction.user)

        fake_channel = interaction.channel

        referenced_message = FakeMessage(fake_guild, member, [])
        reference = FakeReference(resolved=referenced_message)

        pokemeow_bot = discord.Object(id=1234567890)
        pokemeow_bot.name = "PokéMeow"
        fake_message = FakeMessage(
            fake_guild, pokemeow_bot, [embed], reference=reference
        )
        fake_message.channel = fake_channel

        await catch_and_fish_message_rare_spawn_handler(
            self.bot, fake_message, fake_message
        )

        await interaction.response.send_message(
            "Test rare spawn triggered!", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(TestRareSpawn(bot))
