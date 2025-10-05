import discord
from discord import app_commands
from discord.ext import commands

from config.settings import Channels
from utils.db.missing_pokemon_db_func import (
    fetch_user_missing_dict,
    fetch_user_missing_pokemon,
    remove_all_missing_for_user,
    remove_missing_pokemon,
    fetch_user_missing_list
)
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# ❀─────────────────────────────────────────❀
#      💖  Remove Missing Pokémon Function
# ❀─────────────────────────────────────────❀
async def missing_pokemon_remove_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    pokemon: str | int, # Pokemon but its dex number or all
):
    """Remove a or all of the user's missing Pokémon entries."""
    user = interaction.user
    user_id = user.id
    user_name = user.name

    handler = await pretty_defer(
        interaction=interaction,
        content="Processing your removal request...",
        ephemeral=True,
    )
    guild = interaction.guild
    log_channel = guild.get_channel(Channels.bot_logs)

    # 🌸 Remove all missing Pokémon
    if pokemon.lower() == "all":
        entries = await fetch_user_missing_list(bot, user_id)
        if not entries:
            await handler.error("You have no missing Pokémon entries to remove.")
            return

        count = len(entries)
        await remove_all_missing_for_user(bot, user)

        embed = discord.Embed(
            title="🐰 Missing Pokémon Removed",
            description=f"Successfully removed all **{count}** of your missing Pokémon entries. 🌷",
        )
        footer_text = "🌸 All missing Pokémon entries successfully removed."

        embed = await design_embed(embed=embed, user=user, footer_text=footer_text)
        await handler.success(embed=embed, content="")

        if log_channel:
            log_embed = discord.Embed(
                title="🐰 Missing Pokémon Removed",
                description=f"{user.display_name} has removed all their **{count}** missing Pokémon entries.",
            )
            log_embed = await design_embed(embed=log_embed, user=user)
            await log_channel.send(embed=log_embed)

    # 🌸 Remove specific Dex entry
    else:
        dex = int(pokemon)
        entry = await fetch_user_missing_pokemon(bot, user, dex)
        if not entry:
            await handler.error(f"You have no missing Pokémon entry for Dex {dex}.")
            return

        await remove_missing_pokemon(bot, user, dex)
        pokemon_name = entry.get("pokemon_name")
        channel_id = entry.get("channel_id")
        channel = guild.get_channel(channel_id)
        role_id = entry.get("role_id")
        role = guild.get_role(role_id) if role_id else None

        embed = discord.Embed(
            title="🐰 Missing Pokémon Removed",
            description=f"Successfully removed your missing Pokémon entry for **{pokemon_name}** (#{dex}).",
        )
        footer_text = "✨ Missing entry successfully removed from your list."

        embed = await design_embed(
            embed=embed, user=user, pokemon_name=pokemon_name, footer_text=footer_text
        )
        await handler.success(embed=embed, content="")

        if log_channel:
            desc = f"User: {user.display_name}\nPokémon: {pokemon_name} (#{dex})\n Channel:{channel.mention}"
            if role:
                desc += f"\n Role: {role.mention}"
            log_embed = discord.Embed(
                title="🐰 Missing Pokémon Entry Removed",
                description=desc,
            )
            log_embed = await design_embed(embed=log_embed, user=user)
            await log_channel.send(embed=log_embed)
