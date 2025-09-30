# 💗────────────────────────────────────────────
#           🌸 Market Alert Brain (Pretty Defer) 🌸
# 💗────────────────────────────────────────────

import asyncio
from datetime import datetime
from typing import Optional

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.market_alert.market_alert_db_func import insert_name_alert
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.parsers import parse_special_mega_input, resolve_pokemon_input
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


async def add_market_alert_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: int,
    channel: discord.TextChannel,
    role: Optional[discord.Role] = None,
    mobile_role_input: Optional[str] = None,
    notify: bool = True,
):
    """
    Market alert workflow using pretty_defer:
    - Immediate loader with safe edits
    - Updates steps live
    - Sends final confirmation embed
    """
    from utils.cache.market_alert_cache import get_user_alert_count, insert_alert

    PokeCoin = Emojis.PokeCoin
    user = interaction.user
    user_id = user.id
    user_name = user.name
    guild = interaction.guild
    count = get_user_alert_count(user_id)

    loader = await pretty_defer(
        interaction=interaction, content="Processing your new alert...", ephemeral=False
    )

    log_channel = guild.get_channel(Channels.bot_logs)
    if not log_channel:
        await loader.error(content="Bot log channel not found.")
        return

    # 🌸 Normalize role
    role_obj = role
    role_id = None
    role_mention = ""
    if mobile_role_input:
        try:
            mobile_id = int(mobile_role_input.strip().strip("<@&>"))
            role_obj = interaction.guild.get_role(mobile_id)
            if role_obj is None:
                raise ValueError(f"Role ID {mobile_id} not found in guild.")
        except Exception as e:
            await loader.error(
                content=f"❌ Invalid mobile role input: {e}",
            )
            return
    if role_obj:
        role_id = role_obj.id
        role_mention = f" <@&{role_id}>"

    pokemon_title = pokemon.title()

    try:
        # 🔹 Step 1: Resolve Pokémon
        await loader.edit(content="Resolving Pokémon...")
        if pokemon.isdigit():
            if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
                raise ValueError("Invalid 4-digit Dex number.")
            target_name, dex_number = resolve_pokemon_input(pokemon)
        elif any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            dex_number = parse_special_mega_input(pokemon)
            target_name = pokemon_title
        else:
            target_name, dex_number = resolve_pokemon_input(pokemon)

        # 🔹 Step 2: Validate max price
        await loader.edit(content="Validating max price...")
        max_price_int = int(max_price)

        # 🔹 Step 3: Insert into DB
        await loader.edit(content="Inserting alert into DB...")
        await insert_name_alert(
            bot,
            user_id,
            user_name,
            target_name,
            dex_number,
            max_price_int,
            channel.id,
            role_id,
            notify,
        )
        alert_entry = {
            "pokemon": target_name.lower(),
            "dex_number": dex_number,
            "max_price": max_price_int,
            "channel_id": channel.id,
            "role_id": role_id,
            "notify": notify,
            "user_id": user_id,
        }
        # 🔹 Step 4: Refresh cache
        await loader.edit(content="Adding alert to cache...")
        insert_alert(alert=alert_entry)

        # 🔹 Step 5: Increment alerts used
        await loader.edit(content="Finalizing...")

    except Exception as e:
        pretty_log("critical", f"Market alert failed: {e}", exc=e)
        await loader.error(
            content=f"Market alert Add failed: {e}",
        )
        return

    target_name = target_name.title()

    desc_lines = [
        f"- **Member:** {user.mention}",
        f"- **Pokemon:** {target_name} #{dex_number}",
        f"- **Max Price:** {PokeCoin} {max_price_int:,}",
        f"- **Channel:** {channel.mention}",
    ]
    if role_id:
        desc_lines.append(f"- Role: {role_mention}")

    full_desc = "\n".join(desc_lines)

    # 🌸 Build final confirmation embed
    count = count + 1
    display_count = f"Total Alerts: {count}"
    user_embed = discord.Embed(
        title=f"Market Alert Added!",
        description=f"{display_count}\n{full_desc}",
    )

    footer_text = "You'll be notified when a Pokémon matches your alert 🌸"
    user_embed = await design_embed(
        embed=user_embed,
        user=user,
        pokemon_name=target_name,
        footer_text=footer_text,
    )

    if log_channel:
        desc_lines = [
            f"{display_count}\n",
            f"- **Member:** {user.mention}",
            f"- **Pokemon:** {target_name} #{dex_number}",
            f"- **Max Price:** {PokeCoin} {max_price_int:,}",
            f"- **Channel:** {channel.mention}",
        ]
        if role_id:
            desc_lines.append(f"- Role: {role_mention}")

        full_desc = "\n".join(desc_lines)
        log_embed = discord.Embed(
            title=f"Market Alert Created",
            description=full_desc,
            timestamp=datetime.now(),
        )
        log_embed = await design_embed(
            embed=log_embed, user=user, pokemon_name=target_name
        )

    # 🌸 Stop loader and show final embed
    await loader.success(embed=user_embed, content="")

    # 🌸 Log to staff channel
    try:
        pretty_log(
            "sent",
            f"Market alert created for {target_name} @ {max_price_int}",
        )
        if log_channel:
            await log_channel.send(embed=log_embed)
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to send final embed: {e}",
            exc=e,
            include_trace=True,
        )
