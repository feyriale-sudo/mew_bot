from utils.pokemeow.pokemon_gif import get_pokemon_gif
import discord
from discord.ext import commands
from discord import app_commands
from utils.pokemeow.autocomplete import pokemon_autocomplete

# -------------------- Weakness Cog --------------------
class TestGif(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="test-gif", description="Show a Pokémon's gif"
    )
    @app_commands.describe(pokemon="The Pokémon name or dex number")
    @app_commands.autocomplete(pokemon=pokemon_autocomplete)  # 👈 attach autocomplete
    async def test_gif(self, interaction: discord.Interaction, pokemon: str):
        # pokemon here is already the Choice.value you set in

        gif_url = await get_pokemon_gif(pokemon)
        embed = discord.Embed(title=f"{pokemon.title()}")
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.description = f"❌ Pokémon `{pokemon}` not found."


        await interaction.response.send_message(embed=embed)




# -------------------- Setup --------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(TestGif(bot))
