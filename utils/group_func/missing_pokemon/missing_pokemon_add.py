import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Emojis
from config.settings import CHECKLIST_SETTINGS_MAP, Channels
from config.weakness_chart import weakness_chart
from utils.db.missing_pokemon_db_func import upsert_missing_pokemon
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.parsers import parse_special_mega_input, resolve_pokemon_input
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# 🎀────────────────────────────────────────────
#        🌸 Missing Pokemon Add Func
# ─────────────────────────────────────────────
async def missing_pokemon_add_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
):
    # 🌸 Start defer
    loader = await pretty_defer(
        interaction=interaction,
        content="Adding Pokémon to Checklist...",
        ephemeral=True,
    )
    user = interaction.user
    user_id = user.id
    guild = interaction.guild

    # 🌸 Check if user has checklist settings
    if user_id not in CHECKLIST_SETTINGS_MAP:
        await loader.error(
            content="You do not have checklist settings configured. Please contact an admin."
        )
        return

    # 🌸 Resolve Pokémon input
    pokemon_title = pokemon.title()

    # 🌸 If input is just dex number
    if pokemon.isdigit():
        if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
            # 🌸 Return if input is 4 digit number and doesnt start with 1, 7 or 9
            await loader.error(
                content="Invalid Pokémon input. Please provide a valid name or Dex number."
            )
            return
        target_name, dex_number = resolve_pokemon_input(pokemon)

    # 🌸 If input is Mega Pokemon
    elif any(
        (
            pokemon_title.startswith(f"{prefix}Mega ")
            or pokemon_title.startswith(f"{prefix}Mega-")
        )
        for prefix in ["", "Shiny ", "Golden "]
    ):
        dex_number = parse_special_mega_input(pokemon)
        target_name = pokemon_title

    # 🌸 Else, resolve normally
    else:
        target_name, dex_number = resolve_pokemon_input(pokemon)

    # 🌸 Upsert missing pokemon entry
    channel_id = CHECKLIST_SETTINGS_MAP[user_id]["channel_id"]
    role_id = CHECKLIST_SETTINGS_MAP[user_id]["role_id"]
    channel = guild.get_channel(channel_id)
    role = guild.get_role(role_id) if role_id else None

    try:
        await upsert_missing_pokemon(
            bot=bot,
            user_id=user_id,
            user_name=user.name,
            dex=dex_number,
            pokemon_name=target_name,
            role_id=role_id,
            channel_id=channel_id,
        )
        pretty_log(
            "success",
            f"Added missing Pokémon entry for user {user.name} ({user_id}): {target_name} (Dex {dex_number})",
        )
        # 🌸 Success embed
        target_name = target_name.title()
        desc = f"**Pokemon:** {target_name} #{dex_number}\n**Channel:** {channel.mention}\n"
        if role:
            desc += f"**Role:** {role.mention}\n"
        success_embed = discord.Embed(
            title=f"🐰 Pokémon Added to Checklist!",
            description=desc,
        )
        footer_text = f"🌸 Use /checklist remove to remove this entry."
        success_embed = await design_embed(
            embed=success_embed,
            user=interaction.user,
            footer_text=footer_text,
            pokemon_name=target_name.lower(),
        )
        await loader.success(content="", embed=success_embed)

        # 🌸 Log to bot logs channel
        log_channel = guild.get_channel(Channels.bot_logs)
        if log_channel:
            log_embed = success_embed.copy()
            log_embed.title = "📝 Checklist Pokémon Entry Added"
            log_embed.set_footer(
                text=f"User ID: {user_id}",
                icon_url=guild.icon.url if guild.icon else None,
            )
            await log_channel.send(embed=log_embed)

    except Exception as e:
        await loader.error(
            content="❌ An error occurred while adding your missing Pokémon entry.",
        )
        pretty_log(
            tag="error",
            message=f"Error adding missing Pokémon for user {user.name} ({user_id}): {e}",
        )
        return
