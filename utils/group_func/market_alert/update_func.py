import asyncio
from datetime import datetime
from typing import Optional

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.cache.cache_list import market_alert_cache
from utils.group_func.market_alert.market_alert_db_func import (
    insert_name_alert,
    update_market_alert,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.parsers import parse_special_mega_input, resolve_pokemon_input
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


async def update_market_alert_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: int = None,
    channel: discord.TextChannel | None = None,
    role: discord.Role | None = None,
    mobile_role_input: str = None,
    notify: bool | None = None,
):
    """
    Update an existing market alert. Sends the embed directly to the interaction.
    Only updates columns for which a new value is provided.
    """
    from utils.cache.market_alert_cache import insert_alert, remove_alert

    user = interaction.user
    user_id = user.id
    channel_id = channel.id if channel else None
    role_obj = role
    role_id = role.id if role else None

    # ── Normalize mobile role input ──
    if mobile_role_input:
        try:
            mobile_id = int(mobile_role_input.strip().strip("<@&>"))
            role_obj = interaction.guild.get_role(mobile_id)
            if role_obj is None:
                raise ValueError(f"Role ID {mobile_id} not found in guild.")
            role_id = role_obj.id
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Invalid mobile role input: {e}", ephemeral=True
            )
            return

    if all(v is None for v in [max_price, channel_id, role_id, notify]):
        await interaction.response.send_message(
            "❌ No new values provided for update.", ephemeral=True
        )
        return

    # ── Start pretty defer loader ──
    loader = await pretty_defer(
        interaction, content="Updating market alert...", ephemeral=True
    )

    try:
        # ── Resolve Pokémon name & Dex ──
        pokemon_name, dex_number = resolve_pokemon_input(pokemon)

        # ── Prepare updates dictionary ──
        updates = {}
        if max_price is not None:
            updates["max_price"] = int(max_price)
        if channel_id is not None:
            updates["channel_id"] = channel_id
        if role_id is not None:
            updates["role_id"] = role_id
        if notify is not None:
            if isinstance(notify, str):
                notify = notify.lower() in ("true", "1", "t", "yes")
            updates["notify"] = notify

        # ── Perform the update ──
        await loader.edit(content="Applying updates to database...")
        updated_count = await update_market_alert(
            bot, user_id=user_id, dex_number=dex_number, pokemon=pokemon_name, **updates
        )

        await loader.edit(content="Updating alert in cache...")

        # ── Determine existing alert channel in cache ──
        old_channel = next(
            (
                a["channel_id"]
                for a in market_alert_cache
                if a["pokemon"].lower() == pokemon_name.lower()
                and a.get("user_id") == user_id
            ),
            None,
        )

        # Prepare only non-None updates for cache
        cache_updates = {k: v for k, v in updates.items() if v is not None}

        if channel_id and channel_id != old_channel:
            # Channel changed: remove old alert and insert new one
            if old_channel:
                remove_alert(
                    pokemon_name=pokemon_name, channel_id=old_channel, user_id=user_id
                )

            insert_alert(
                {
                    "user_id": user_id,
                    "pokemon": pokemon_name.lower(),
                    "dex_number": dex_number,
                    "channel_id": channel_id,
                    **cache_updates,
                }
            )
        else:
            # Update in-place
            if old_channel:
                insert_alert(
                    {
                        "user_id": user_id,
                        "pokemon": pokemon_name.lower(),
                        "dex_number": dex_number,
                        "channel_id": old_channel,
                        **cache_updates,
                    }
                )

    except Exception as e:
        pretty_log(
            "error",
            f"Failed updating market alert for {user_id}: {e}",
            exc=e,
            include_trace=True,
        )
        await loader.error(content=f"An unexpected error occurred: {e}")
        return

    # ── Build confirmation embed ──
    description = f"- **Pokemon:** {pokemon_name.title()} (Dex #{dex_number})\n"

    # Only add Updated Fields section if something changed
    updated_fields = []
    if max_price is not None:
        updated_fields.append(f"**Max Price:** {Emojis.PokeCoin} {max_price:,}")
    if channel_id is not None:
        updated_fields.append(f"**Channel:** <#{channel_id}>")
    if role_id is not None:
        updated_fields.append(f"**Role:** <@&{role_id}>")
    if notify is not None:
        notify_display = "Enable" if notify else "Disable"
        updated_fields.append(f"**Notify:** {notify_display}")

    if updated_fields:
        description += f"\n**Updated Fields:**\n" + "\n".join(updated_fields)

    embed = discord.Embed(
        title=f"Market Alert Updated!", description=description, color=0xFF99FF
    )

    footer_text = "You'll be notified according to your updated alert settings"
    embed = await design_embed(
        embed=embed, user=user, pokemon_name=pokemon_name, footer_text=footer_text
    )

    # ── Stop loader and show final embed ──
    await loader.success(embed=embed, content="")

    pretty_log(
        "sent",
        f"Updated {updated_count} alerts for user: {user.name} -> {pokemon_name.title()} (Dex #{dex_number})",
    )
