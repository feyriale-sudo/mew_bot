import asyncio
from datetime import datetime
from typing import Optional

import discord

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.market_alert.market_alert_db_func import (
    fetch_user_alerts,
    remove_all_market_alerts,
    remove_market_alert,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.parsers import parse_special_mega_input, resolve_pokemon_input
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


async def remove_market_alert_func(bot, interaction: discord.Interaction, pokemon: str):
    """
    Removes a market alert for a user.
    Uses pretty_defer loader: runs full workflow first, then updates loader once with final result.
    """

    from utils.cache.market_alert_cache import (
        get_user_alert_count,
        remove_all_alerts_from_user,
    )

    user = interaction.user
    user_id = user.id
    removed_alerts: list[tuple[str, str]] = []
    footer_text = "🌸 You will no longer receive alerts for these Pokémon"

    # 🌸 Start loader
    loader = await pretty_defer(
        interaction, content="Processing market alert removal..."
    )

    try:
        # 🌸 SEPARATE BRANCH FOR "ALL"
        if pokemon.lower() == "all":
            # 🌸 Fetch all alerts
            user_alerts = await fetch_user_alerts(bot, user_id)

            if not user_alerts:
                await loader.error(content=f"You have no active market alerts.")
                return

            removed_alerts = [
                (alert["pokemon"].title(), alert["dex_number"]) for alert in user_alerts
            ]

            # 🌸 Remove all alerts
            await remove_all_market_alerts(bot, user_id)

            # 🌸 Remove all alerts from cache
            remove_all_alerts_from_user(user_id=user_id)

        else:
            # 🌸 EXISTING SINGLE POKÉMON LOGIC
            pokemon_title = pokemon.title()
            if pokemon.isdigit():
                target_key = pokemon
            else:
                target_key = pokemon_title

            try:
                if any(
                    pokemon_title.startswith(f"{prefix}Mega ")
                    for prefix in ["", "Shiny ", "Golden "]
                ):
                    target_name = pokemon_title
                    dex_number = parse_special_mega_input(pokemon)
                else:
                    for prefix in ["Shiny ", "Golden "]:
                        if pokemon_title.startswith(prefix):
                            target_name = pokemon_title
                            _, dex_number = resolve_pokemon_input(pokemon_title)
                        else:
                            target_name, dex_number = resolve_pokemon_input(
                                pokemon_title
                            )
            except ValueError as e:
                raise ValueError(f"{e}")

            # 🌸 Check if alert exists before trying to remove
            user_alerts = await fetch_user_alerts(bot, user_id)
            exists = False
            for alert in user_alerts:
                if pokemon.isdigit() and alert["dex_number"] == int(pokemon):
                    exists = True
                    break
                elif (
                    not pokemon.isdigit()
                    and alert["pokemon"].lower() == target_name.lower()
                ):
                    exists = True
                    break

            if not exists:
                await loader.error(
                    content=f"No active alert found for **{pokemon_title}**."
                )
                return

            # 🌸 Remove the alert
            if pokemon.isdigit():
                removed_count = await remove_market_alert(bot, user_id, pokemon)
                if removed_count > 0:
                    removed_alerts.append((target_name.title(), pokemon))

                    # 🌸 Remove single alert from cache
                    alert = next(
                        (a for a in user_alerts if a["dex_number"] == int(pokemon)),
                        None,
                    )
                    if alert:
                        remove_alert(
                            pokemon_name=alert["pokemon"],
                            channel_id=alert["channel_id"],
                            user_id=user_id,
                        )

            else:
                removed_count = await remove_market_alert(
                    bot, user_id, target_name.lower()
                )
                if removed_count > 0:
                    removed_alerts.append((target_name.title(), dex_number))

                    # 🌸 Remove single alert from cache
                    from utils.cache.market_alert_cache import remove_alert

                    alert = next(
                        (
                            a
                            for a in user_alerts
                            if a["pokemon"].lower() == target_name.lower()
                        ),
                        None,
                    )
                    if alert:
                        remove_alert(
                            pokemon_name=alert["pokemon"],
                            channel_id=alert["channel_id"],
                            user_id=user_id,
                        )

            count = get_user_alert_count(user_id)
            display_count = f"Total Alerts: {count}"
            status_message = display_count

    except Exception as e:
        await loader.error(content=f"Failed to remove alert: {e}")
        pretty_log("critical", f"Failed to remove alert: {e}", source="MarketAlert")
        return

    # 🌸 Build final embed
    status_line = status_message
    member_line = f"- Member: {user.mention}"

    if removed_alerts:
        if len(removed_alerts) == 1:
            name, dex = removed_alerts[0]
            removed_line = f"- Removed Pokémon: {name} #{dex}"
        else:
            removed_line = f"Removed Pokémon(s):\n" + "\n".join(
                [f"> - {name} #{dex}" for name, dex in removed_alerts]
            )

        user_embed = discord.Embed(
            title=f"Market Alert Removed",
            description=f"{status_line}\n{member_line}\n{removed_line}",
        )
        user_embed = await design_embed(
            embed=user_embed,
            user=user,
            footer_text=footer_text,
            pokemon_name=name,
        )
    else:
        user_embed = discord.Embed(
            title="❌ No Alert Found",
            description=f"No active alert found for **{pokemon.title()}**.",
            color=0xFF80A5,
        )

    # 🌸 Log embed
    log_channel = interaction.guild.get_channel(Channels.bot_logs)

    if removed_alerts and log_channel:
        log_description = f"Alert(s) Removed\n".join(
            [f"> - {name} #{dex}" for name, dex in removed_alerts]
        )
        log_embed = discord.Embed(
            title=f"Market Alert Removed",
            description=f"{status_message}\n-Member: {user.mention}\n- Pokemon:\n{log_description}",
            color=0xFF80A5,
            timestamp=datetime.now(),
        )
        log_embed = await design_embed(
            embed=log_embed,
            user=user,
            pokemon_name=name,
        )

    # 🌸 Stop loader and show final embed
    await loader.success(content=f"{user.mention}", embed=user_embed)
    pretty_log(
        "sent",
        f"Removed {len(removed_alerts)} market alert(s) for user {user_id}",
    )

    if log_channel and removed_alerts:
        await log_channel.send(embed=log_embed)
