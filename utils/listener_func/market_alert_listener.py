# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.aesthetic import Emojis
from config.settings import *
from utils.cache.cache_list import _market_alert_index, market_alert_cache
from utils.logs.debug_logs import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log

PokeCoin = Emojis.PokeCoin

ALLOWED_WEBHOOKS = {
    1422430564102836370,  # Regular
    1422430809679466516,  # Legendary
    1422431013920837633,  # Shiny
    1422431171639378043,  # Golden
}

# 🔹 Global role cache (guild_id, role_id) -> discord.Role
_role_cache: dict[tuple[int, int], discord.Role] = {}


# enable_debug(f"{__name__}.process_market_alert_message")


async def process_market_alert_message(
    bot: discord.Client, message: discord.Message, market_category_id: int
):
    debug_log("Entered process_market_alert_message()", highlight=True)

    if message.channel.category_id != market_category_id:
        debug_log(
            f"Skipped: channel {message.channel.id} not in category {market_category_id}"
        )
        return
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        debug_log(f"Skipped: webhook {message.webhook_id} not allowed")
        return
    if not message.embeds:
        debug_log("Skipped: no embeds in message")
        return

    embed = message.embeds[0]
    embed_author_name = embed.author.name if embed.author else ""
    debug_log(f"Embed author parsed: {embed_author_name!r}")

    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        debug_log("Skipped: could not extract name + dex from author")
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))
    debug_log(f"Extracted Pokémon: {poke_name} (Dex {poke_dex})")

    fields = {f.name: f.value for f in embed.fields}
    debug_log(f"Embed fields extracted: {list(fields.keys())}")

    listed_price_str = re.sub(r"<a?:\w+:\d+>", "", fields.get("Listed Price", "0"))
    match_price = re.search(r"(\d[\d,]*)", listed_price_str)
    listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0
    debug_log(f"Parsed listed price: {listed_price}")

    # Rebuild index if empty
    if not _market_alert_index:
        debug_log("Rebuilding market alert index...")
        _market_alert_index.clear()
        for alert in market_alert_cache:
            key = alert["pokemon"].lower()
            _market_alert_index.setdefault(key, []).append(alert)
        debug_log(f"Market alert index rebuilt: {len(_market_alert_index)} entries")

    original_id = fields.get("ID", "0")

    # ✅ O(1) lookup
    alerts_to_check = _market_alert_index.get(poke_name.lower(), [])
    debug_log(f"Found {len(alerts_to_check)} alerts for {poke_name}")

    if not alerts_to_check:
        debug_log("Fallback: scanning full cache")
        alerts_to_check = [
            alert
            for alert in market_alert_cache
            if alert["pokemon"].lower() == poke_name.lower()
        ]
        debug_log(f"Fallback found {len(alerts_to_check)} alerts")

    for alert in alerts_to_check:
        debug_log(
            f"Checking alert {alert['user_id']} for {alert['pokemon']}", highlight=True
        )

        if not alert.get("notify", True):
            debug_log("Skipped alert: notify=False")
            continue
        if int(alert["dex_number"]) != poke_dex:
            debug_log(
                f"Skipped alert: dex mismatch ({alert['dex_number']} vs {poke_dex})"
            )
            continue
        if listed_price > alert["max_price"]:
            debug_log(f"Skipped alert: price {listed_price} > max {alert['max_price']}")
            continue

        channel = bot.get_channel(alert["channel_id"])
        if not channel:
            try:
                channel = await bot.fetch_channel(alert["channel_id"])
            except Exception as e:
                pretty_log(
                    "warn", f"Failed to fetch channel {alert['channel_id']}: {e}"
                )
                continue
        debug_log(f"Resolved channel {channel.id} for alert")

        # Build embed
        new_embed = discord.Embed(color=embed.color or 0x0855FB)
        if embed.thumbnail:
            new_embed.set_thumbnail(url=embed.thumbnail.url)
        new_embed.set_author(
            name=embed_author_name,
            icon_url=embed.author.icon_url if embed.author else None,
        )

        new_embed.add_field(
            name="Buy Command (iPhone)", value=f"`;m b {original_id}`", inline=False
        )
        new_embed.add_field(
            name="Buy Command (Android)", value=f";m b {original_id}", inline=False
        )

        for name, value in fields.items():
            if name == "ID":
                continue
            value_cleaned = re.sub(r"<a?:\w+:\d+>", PokeCoin, value)
            new_embed.add_field(name=name, value=value_cleaned)

        new_embed.set_footer(
            text=(
                embed.footer.text
                if embed.footer
                else "Please check listing before purchase"
            )
        )

        content = ""
        if alert.get("role_id"):
            guild = bot.get_guild(MAIN_SERVER_ID)
            if guild:
                role_key = (guild.id, alert["role_id"])
                role = _role_cache.get(role_key) or guild.get_role(alert["role_id"])
                if role:
                    _role_cache[role_key] = role
                    content += role.mention + " "
                    debug_log(f"Attached role mention: {role.name}")

        content += f"{poke_name} on market for {PokeCoin} {listed_price:,}"

        try:
            await channel.send(content=content, embed=new_embed)
            pretty_log(
                "info",
                f"Sent market alert for {poke_name} #{poke_dex} to channel {alert['channel_id']}",
            )
        except Exception as e:
            pretty_log("error", f"Failed to send market alert: {e}")
