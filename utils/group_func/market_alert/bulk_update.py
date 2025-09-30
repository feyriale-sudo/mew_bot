import asyncio
from datetime import datetime
from typing import Optional

import discord

from config.aesthetic import *
from utils.cache.cache_list import market_alert_cache
from utils.group_func.market_alert.market_alert_db_func import (
    update_user_alerts_channel_or_role,
)
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


async def update_market_alert_role_channel_func(
    bot,
    interaction: discord.Interaction,
    channel: discord.TextChannel | None = None,
    role: str | None = None,
):
    """
    Updates all of a user's market alerts with a new channel and/or role.
    Sends the embed directly to the interaction.
    Supports removing the role by passing 'none' or None.
    """
    from utils.cache.market_alert_cache import update_user_alerts_in_cache

    user = interaction.user
    user_id = user.id

    # 💜 Start pretty defer loader
    loader = await pretty_defer(
        interaction, content="Updating bulk alerts...", ephemeral=True
    )

    # ── Determine role ID ──
    role_id: int | None = None
    if isinstance(role, discord.Role):
        role_id = role.id
    elif isinstance(role, str) and role.lower() != "none":
        # Normalize role from mobile_role_input-like string
        try:
            mobile_id = int(role.strip().strip("<@&>"))
            role_obj = interaction.guild.get_role(mobile_id)
            if role_obj is None:
                raise ValueError(f"Role ID {mobile_id} not found in guild.")
            role_id = role_obj.id
        except Exception as e:
            await loader.error(content=f"Invalid role input: {e}")
            return
    # Else role is None or "none", leave role_id as None to remove

    # ── Determine channel ID ──
    channel_id = channel.id if channel else None

    if channel_id is None and role_id is None and role != "none":
        await loader.error(
            content="You must provide at least a new channel or role to update."
        )
        return

    # ── Update database ──
    try:
        updated_count = await update_user_alerts_channel_or_role(
            bot, user_id=user_id, channel_id=channel_id, role_id=role_id
        )

        update_user_alerts_in_cache(
            user_id=user_id, new_channel_id=channel_id, new_role_id=role_id
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed bulk updating alerts for {user_id}: {e}",
            exc=e,
            include_trace=True,
        )
        await loader.error(content=f"An unexpected error occurred: {e}")
        return

    # ── Build confirmation embed ──
    description_parts = []
    if channel_id is not None:
        description_parts.append(f"Channel updated to <#{channel_id}>")
    if role_id is not None:
        description_parts.append(f"Role updated to <@&{role_id}>")
    elif role == "none" or role is None:
        description_parts.append("Role removed")

    description_text = "\n".join(description_parts)
    embed = discord.Embed(
        title=f"Market Alerts Bulk Updated!",
        description=f"{updated_count} alert(s) successfully updated!\n{description_text}",
        color=0xFF80A5,
    )
    footer_text = "You'll be notified according to your updated alert settings"
    embed = await design_embed(
        embed=embed,
        user=user,
        footer_text=footer_text,
    )
    # 💜 Stop loader and show final embed
    await loader.success(embed=embed, content="")

    pretty_log(
        "sent",
        f"Bulk updated {updated_count} alerts for user {user_id}",
    )
