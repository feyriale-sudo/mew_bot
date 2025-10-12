# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.aesthetic import Emojis
from config.rarity import rarity_meta
from config.settings import *
from utils.cache.cache_list import (
    _market_alert_index,
    _missing_pokemon_index,
    market_alert_cache,
    market_value_cache,
    missing_pokemon_cache,
)
from utils.logs.pretty_log import pretty_log
from utils.db.market_value_db_func import set_market_value

PokeCoin = Emojis.PokeCoin

ALLOWED_WEBHOOKS = {
    1422430564102836370,  # Regular
    1422430809679466516,  # Legendary
    1422431013920837633,  # Shiny
    1422431171639378043,  # Golden
}

HIGH_VALUE_RARITY_COLOR_LIST = [
    rarity_meta["legendary"]["color"],
    rarity_meta["shiny"]["color"],
    rarity_meta["event_exclusive"]["color"],
    rarity_meta["golden"]["color"],
    rarity_meta["gigantamax"]["color"],
]
OTHER_EXCLUSIVES = [
    "chingling",
    "mimikyu",
    "mimejr",
    "happiny",
    "chatot",
    "munchlax",
    "riolu",
    "audino",
    "zorua",
    "emolga",
    "ferroseed",
    "golett",
    "pawniard",
    "pancham",
    "spritzee",
    "swirlix",
    "noibat",
    "crabrawler",
    "rockruff",
    "type-null",
    "yamper",
    "nickit",
    "carbink",
]
HIGH_VALUE_PREFIX = [
    "mega ",
    "shiny mega ",
    "gigantamax-",
    "shiny gigantamax-",
    "eternamax-",
    "shiny eternamax-",
]
# 🔹 Cache for roles
_role_cache: dict[tuple[int, int], discord.Role] = {}


# 💜────────────────────────────────────────────
#   Process Market + Missing Pokémon Alerts
# 💜────────────────────────────────────────────
async def process_market_alert_message(
    bot: discord.Client, message: discord.Message, market_category_id: int
):
    """Send alerts for Pokémon listed on market and/or missing Pokémon entries."""
    if message.channel.category_id != market_category_id:
        return
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        pretty_log("debug", f"Message from unallowed webhook: {message.webhook_id}")
        return
    if not message.embeds:
        pretty_log("debug", "Message has no embeds")
        return

    embed = message.embeds[0]
    embed_author_name = embed.author.name if embed.author else ""

    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        pretty_log("debug", f"Could not parse embed author name: {embed_author_name}")
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))
    fields = {f.name: f.value for f in embed.fields}

    listed_price_str = re.sub(r"<a?:\w+:\d+>", "", fields.get("Listed Price", "0"))
    match_price = re.search(r"(\d[\d,]*)", listed_price_str)
    listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0
    original_id = fields.get("ID", "0")
    embed_color = embed.color.value


    # 💎────────────────────────────────────────────
    #           🏪 Update Market Value Cache & DB
    # 💎────────────────────────────────────────────
    # If in high value rarity color list or in other exclusives, cache value
    if (
        embed_color in HIGH_VALUE_RARITY_COLOR_LIST
        or poke_name.lower() in OTHER_EXCLUSIVES
        or any(prefix in poke_name.lower() for prefix in HIGH_VALUE_PREFIX)
    ):
        # Extract additional market data
        lowest_market_str = re.sub(
            r"<a?:\w+:\d+>", "", fields.get("Lowest Market", "0")
        )
        lowest_market_match = re.search(r"(\d[\d,]*)", lowest_market_str)
        lowest_market = (
            int(lowest_market_match.group(1).replace(",", ""))
            if lowest_market_match
            else 0
        )

        listing_seen = fields.get("Listing Seen", "Unknown")

        # Upsert into market value cache
        cache_key = poke_name.lower()

        # Get existing data to preserve true lowest price
        existing_data = market_value_cache.get(cache_key, {})
        existing_lowest = existing_data.get("true_lowest", float("inf"))

        # Calculate the true lowest price among:
        # 1. Current listing price
        # 2. "Lowest Market" from embed
        # 3. Previously tracked lowest
        true_lowest = min(listed_price, lowest_market, existing_lowest)

        # Only update if we have a valid price (not 0)
        if true_lowest == float("inf") or true_lowest == 0:
            true_lowest = (
                max(listed_price, lowest_market)
                if max(listed_price, lowest_market) > 0
                else 0
            )

        # Update cache
        market_value_cache[cache_key] = {
            "pokemon": poke_name,
            "dex": poke_dex,
            "rarity": "unknown",  # Could extract from footer if available
            "lowest_market": lowest_market,  # Original "Lowest Market" from embed
            "current_listing": listed_price,
            "true_lowest": true_lowest,  # Our calculated true lowest
            "listing_seen": listing_seen,
        }

        # Update database immediately for high-value Pokémon
        await set_market_value(
            bot,
            pokemon_name=poke_name,
            dex_number=poke_dex,
            rarity="unknown",
            lowest_market=lowest_market,
            current_listing=listed_price,
            true_lowest=true_lowest,
            listing_seen=listing_seen,
        )

        pretty_log(
            "debug",
            f"Updated market cache & DB for {poke_name}: embed_lowest={lowest_market:,}, current={listed_price:,}, true_lowest={true_lowest:,}, seen={listing_seen}",
        )

    # 🧩 Build Market Index (if needed) - Fix the indexing structure
    # The cache loader uses 3-tuples, but we need pokemon-name lookup
    temp_index = {}
    for alert in market_alert_cache:
        key = alert["pokemon"].lower()
        temp_index.setdefault(key, []).append(alert)

    # 💼 Lookup both Market + Missing
    alerts_to_check = temp_index.get(poke_name.lower(), [])
    missing_matches = [
        m
        for m in missing_pokemon_cache
        if m.get("pokemon_name", "").lower() == poke_name.lower()
    ]

    # 🩵 Combine users from both caches
    all_user_ids = {a["user_id"] for a in alerts_to_check} | {
        m["user_id"] for m in missing_matches
    }

    # Debug logging to help troubleshoot
    if poke_name.lower() == "weedle":
        pretty_log("debug", f"Cache has {len(market_alert_cache)} total alerts")
        pretty_log("debug", f"Found {len(alerts_to_check)} Weedle alerts")
        for i, alert in enumerate(alerts_to_check):
            pretty_log(
                "debug",
                f"  Alert {i+1}: max_price={alert.get('max_price')}, user_id={alert.get('user_id')}",
            )
        if not alerts_to_check:
            pretty_log(
                "debug",
                f"Available pokemon in cache: {list(set(alert.get('pokemon', '') for alert in market_alert_cache[:10]))}",
            )

    for user_id in all_user_ids:
        # Identify state
        market_alert_entry = next(
            (a for a in alerts_to_check if a["user_id"] == user_id), None
        )
        missing_entry = next(
            (m for m in missing_matches if m["user_id"] == user_id), None
        )

        has_market = bool(market_alert_entry)
        has_missing = bool(missing_entry)

        # 🌷 Skip empty
        if not (has_market or has_missing):
            continue

        # 💸 Skip overpriced market alerts only if NOT also missing
        if (
            has_market
            and not has_missing
            and listed_price > market_alert_entry["max_price"]
        ):
            pretty_log(
                "skip",
                f"Skipped alert for {poke_name}: listed price {listed_price:,} > max {market_alert_entry['max_price']:,} (user {user_id}) [market only]",
            )
            continue
        elif (
            has_market
            and has_missing
            and listed_price > market_alert_entry["max_price"]
        ):
            pretty_log(
                "info",
                f"Ignored price limit for {poke_name} (listed {listed_price:,}, max {market_alert_entry['max_price']:,}) because it's also missing for user {user_id}",
            )

        # 🪞 Channel logic
        if has_market and has_missing:
            target_channel_id = market_alert_entry["channel_id"]
        elif has_market:
            target_channel_id = market_alert_entry["channel_id"]
        else:
            target_channel_id = missing_entry["channel_id"]

        # 🧾 Build embed
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

        # 🌸 Footer message
        if has_market and has_missing:
            footer_note = "This Pokémon is also missing from your box! 🌷"
        elif has_missing:
            footer_note = "This Pokémon is missing from your box! 🌸"
        else:
            footer_note = "Please check listing before purchase 💫"
        new_embed.set_footer(text=footer_note)

        # 🩵 Try to fetch channel safely
        channel = bot.get_channel(target_channel_id)
        if not channel:
            try:
                channel = await bot.fetch_channel(target_channel_id)
            except Exception as e:
                pretty_log(
                    "warn",
                    f"Failed to fetch channel {target_channel_id} for user {user_id}: {e}",
                )
                continue

        # 🏷️ Determine which role to ping
        if has_market and has_missing:
            target_role_id = market_alert_entry.get("role_id")
        elif has_market:
            target_role_id = market_alert_entry.get("role_id")
        else:
            target_role_id = missing_entry.get("role_id")

        # 🪞 Try to resolve role safely (cache-friendly)
        role_mention = ""
        if target_role_id:
            guild = channel.guild
            if guild:
                role = _role_cache.get((guild.id, target_role_id))
                if not role:
                    try:
                        role = guild.get_role(target_role_id) or await guild.fetch_role(
                            target_role_id
                        )
                        _role_cache[(guild.id, target_role_id)] = role
                    except Exception as e:
                        pretty_log(
                            "warn",
                            f"Failed to fetch role {target_role_id} in guild {guild.id}: {e}",
                        )
                if role:
                    role_mention = role.mention

        # 💬 Compose message
        content = (
            f"{role_mention} {poke_name} on market for {PokeCoin} {listed_price:,}"
        )
        if has_missing and not has_market:
            content = f"{role_mention} {poke_name} on market for {PokeCoin} {listed_price:,} — and it's missing from your box!"
        elif has_market and has_missing:
            content = f"{role_mention} {poke_name} is on the market for {PokeCoin} {listed_price:,} and is missing from your box too! 🌷"

        # ✨ Send alert
        try:
            await channel.send(content=content.strip(), embed=new_embed)
            pretty_log(
                "info",
                f"Sent alert for {poke_name} (Dex {poke_dex}) → User {user_id} "
                f"[market={has_market}, missing={has_missing}, role={target_role_id}]",
            )
        except Exception as e:
            pretty_log(
                "error", f"Failed to send combined alert for user {user_id}: {e}"
            )
