import re

import discord

from config.aesthetic import Emojis, FACTION_LOGO_EMOJIS
from config.faction_data import get_faction_by_emoji
from utils.cache.cache_list import (
    daily_faction_ball_cache,
    user_info_cache,
    utility_cache,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

FISHING_COLOR = 0x87CEFA


# 🟣────────────────────────────────────────────
# [🎯 FUNCTION] Faction Hunt Listener
# 🟣────────────────────────────────────────────
async def faction_hunt_alert(bot, before: discord.Message, after: discord.Message):
    """Listens to PokéMeow's faction hunt messages for alerts."""

    embed = after.embeds[0] if after.embeds else None
    if not embed:
        return

    description_text = after.embeds[0].description
    if description_text and "<:team_logo:" not in description_text:
        return

    # Regex to match: <:team_logo:ID>
    team_logo_emoji = re.findall(r"<:team_logo:\d+>", description_text)

    if len(team_logo_emoji) != 1:
        return

    embed_faction = (
        get_faction_by_emoji(team_logo_emoji[0]) if team_logo_emoji else None
    )

    if not embed_faction:
        return

    trainer_id = None
    trainer_name = None
    user_id = None
    fishing_user = None

    member = await get_pokemeow_reply_member(before)
    if not member:
        embed_color = after.embeds[0].color
        if embed_color and (
            embed_color.value == FISHING_COLOR or embed_color == FISHING_COLOR
        ):
            if after.reference and getattr(after.reference, "resolved", None):
                resolved_author = getattr(after.reference.resolved, "author", None)
                trainer_id = resolved_author.id if resolved_author else None

            if not trainer_id and after.embeds[0].description:
                name_match = re.search(r"\*\*(.+?)\*\*", after.embeds[0].description)
                if name_match:
                    trainer_name = name_match.group(1)
                    user = discord.utils.find(
                        lambda m: m.display_name == trainer_name,
                        after.guild.members,
                    )
                    fishing_trainer_id = user.id if user else None

            if not trainer_id and not trainer_name:
                return
        else:
            return

    if member:
        user_id = member.id
    elif trainer_id:
        user_id = trainer_id
    elif trainer_name:
        user = discord.utils.find(
            lambda m: m.display_name == trainer_name, after.guild.members
        )
        user_id = user.id if user else None

    # User faction ball alert settings
    user_faction_ball_alert = utility_cache.get(user_id, {}).get("faction_ball_alert")
    if user_faction_ball_alert == "off":
        return

    if not user_faction_ball_alert:
        if trainer_name:
            from utils.cache.utility_cache import get_user_id_by_name

            user_id = get_user_id_by_name(trainer_name)
            user_faction_ball_alert = utility_cache.get(user_id, {}).get(
                "faction_ball_alert"
            )

            if user_id:
                fishing_user = after.guild.get_member(user_id)
        if not user_id:
            return
        if not user_faction_ball_alert:
            return
        if not trainer_name:
            return

    if user_faction_ball_alert == "off":
        return


    embed_faction_emoji = getattr(FACTION_LOGO_EMOJIS, embed_faction)
    print(embed_faction)
    if embed_faction_emoji:
        display_embed_faction = f"{embed_faction_emoji} {embed_faction.title()} faction"
    display_embed_faction = f"{embed_faction.title()} faction"

    user_name = (
        member.display_name
        if member
        else fishing_user.display_name if fishing_user else "Trainer"
    )
    user_mention = (
        member.mention
        if member
        else fishing_user.mention if fishing_user else "Trainer"
    )

    user_faction = user_info_cache.get(user_id, {}).get("faction")
    if not user_faction:
        return

    faction_ball = daily_faction_ball_cache.get(user_faction)
    if not faction_ball:
        content = f"{user_mention} I don't know your faction's daily ball yet, can you do `;fa`? Thanks!."
        await after.channel.send(content=content)
        pretty_log(
            "info",
            f"Could not send faction ball alert to {user_name} ({user_id}) for {embed_faction} daily ball because their faction {user_faction} has no daily ball set.",
        )
        return
    ball_emoji = getattr(Emojis, faction_ball.lower())
    if ball_emoji:
        if user_faction_ball_alert == "on":
            content = f"{Emojis.faction} {user_mention} This Pokémon is from {display_embed_faction}! Use {ball_emoji} to catch it!"
            await after.channel.send(content=content)
            pretty_log(
                "info",
                f"Sent faction ball alert to {user_name} ({user_id}) for {embed_faction} daily ball.",
            )
        elif user_faction_ball_alert == "on_no_pings":
            content = f"{Emojis.faction} {user_name} This Pokémon is from {display_embed_faction}! Use {ball_emoji} to catch it!"
            await after.channel.send(content=content)
            pretty_log(
                "info",
                f"Sent faction ball alert (no ping) to {user_name} ({user_id}) for {embed_faction} daily ball.",
            )
