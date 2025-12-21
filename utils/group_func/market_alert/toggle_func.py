import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.market_alert.market_alert_db_func import (
    insert_name_alert,
    toggle_market_alert_notify,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.new_parsers import resolve_pokemon_input
from utils.visuals.name_helpers import format_display_pokemon_name

async def toggle_market_alert_func(
    bot, interaction: discord.Interaction, pokemon: str, value: bool
):
    """
    Toggle 'notify' on/off for a specific Pokémon/Dex alert or all alerts.
    Sends the resulting embed directly to the interaction.
    """

    from utils.cache.market_alert_cache import update_user_alerts_in_cache

    user = interaction.user
    user_id = user.id
    await interaction.response.defer(ephemeral=True)

    try:
        # ── Handle ALL case ──
        if pokemon.lower() == "all":
            updated_count = await toggle_market_alert_notify(bot, user_id, value, "all")
            # Bulk update cache for this user
            update_user_alerts_in_cache(user_id=user_id, new_notify=value)
            embed = discord.Embed(
                title="🌸 Market Alerts Updated",
                description=f"Toggled **{updated_count} alert(s)** to {'✅ Enabled' if value else '❌ Disabled'}.",
                color=0xFF80A5,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            pretty_log(
                "sent",
                f"Toggled {updated_count} alerts for user {user_id} (ALL)",
            )
            return

        # ── Resolve Pokémon name & Dex ──
        pokemon_title = pokemon.title()
        if any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            target_name = pokemon_title
            try:
                _, dex_number = resolve_pokemon_input(pokemon)
            except ValueError:
                dex_number = None
        else:
            try:
                target_name, dex_number = resolve_pokemon_input(pokemon)
            except ValueError as e:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
                return

        # ── Update notify column ──
        updated_count = await toggle_market_alert_notify(
            bot, user_id, value, target_name
        )

        # Refresh this user’s cache (single update still handled by same function)
        update_user_alerts_in_cache(
            user_id=user_id, new_notify=value, target_pokemon=target_name
        )

        if updated_count == 0:
            embed = discord.Embed(
                title="🌸 No Alert Found",
                description=f"You don’t have any alert for **{target_name} (Dex #{dex_number})**.",
                color=0xFF80A5,
            )
        else:
            display_name = format_display_pokemon_name(target_name)
            embed = discord.Embed(
                title="🌸 Market Alert Toggled",
                description=f"Toggled your alert for **{display_name} (Dex #{dex_number})** "
                f"to {'✅ Enabled' if value else '❌ Disabled'}.",
                color=0xFF80A5,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)
        pretty_log(
            "sent",
            f"Toggled alert for user {user_id} -> {target_name} (Dex #{dex_number})",
        )

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to toggle market alert for user {user_id}: {e}",
            include_trace=True,
        )
        await interaction.followup.send(
            f"❌ An unexpected error occurred: {e}", ephemeral=True
        )
