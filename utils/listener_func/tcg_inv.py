import re
import typing

import discord

from utils.logs.pretty_log import pretty_log


async def extract_username_and_fetch_member(
    guild: discord.Guild, title: str
) -> typing.Optional[discord.Member]:
    """
    Extracts the username before "'s" from a string like "khy.09's Sealed TCG Inventory"
    and fetches the corresponding member object from the guild (case-insensitive).
    Returns None if not found.
    """

    match = re.search(r"([\w.]+)'s", title)
    if not match:
        return None
    username = match.group(1)
    # Try to find member by name (case-insensitive)
    for member in guild.members:
        if member.name.lower() == username.lower() or (
            member.display_name and member.display_name.lower() == username.lower()
        ):
            return member
    return None


_tcg_pack_cache = {}
_tcg_pages_seen = set()
member_obj = None


async def parse_tcg_inventory_embed(
    message: discord.Message,
    user_mention: str = "@user",
):
    """
    Parses a TCG inventory embed, groups pack IDs by category, and batches ;tcg gift commands (20 per message).
    Sends all commands after all pages are processed.
    """
    global _tcg_pack_cache, _tcg_pages_seen, member_obj
    pretty_log(
        tag="debug",
        message=f"parse_tcg_inventory_embed called for message ID: {getattr(message, 'id', None)}",
    )
    if not message or not hasattr(message, "embeds") or not message.embeds:
        pretty_log(tag="debug", message="No embeds found in message.")
        return None

    embed = message.embeds[0]
    desc = embed.description or ""
    footer = embed.footer.text if embed.footer else ""
    embed_color = embed.color if embed else discord.Color.blue()
    embed_title = embed.title if embed else ""
    # pretty_log(tag="debug", message=f"Embed description: {desc}")
    # pretty_log(tag="debug", message=f"Embed footer: {footer}")

    # Extract page number from footer (e.g., 'Page 1 / 4')
    page_match = re.search(r"Page (\d+) / (\d+)", footer)
    if not page_match:
        pretty_log(tag="debug", message="No page info found in footer.")
        return None
    page_num = int(page_match.group(1))
    total_pages = int(page_match.group(2))
    if page_num == 1:
        member = await extract_username_and_fetch_member(
            guild=message.guild, title=embed_title
        )
        if member:
            member_obj = member
            pretty_log(
                tag="debug",
                message=f"Set member_obj to {getattr(member, 'display_name', None)} for user mention {user_mention}.",
            )

    _tcg_pages_seen.add(page_num)
    pretty_log(
        tag="debug",
        message=f"Page {page_num} detected. Pages seen: {_tcg_pages_seen} / {total_pages}",
    )

    # Extract lines with pack info (lines starting with a number and a pack code)
    lines = [l for l in desc.split("\n") if re.match(r"\s*\d+\. ", l)]
    for line in lines:
        # Example line:
        # 1. <:aq_logo:...> <:aq_pack_c:...> `aq-pack-4122` Aquapolis Pack ...
        pack_id_match = re.search(r"`([a-z]+-pack-\d+)`", line)
        if pack_id_match:
            pack_id = pack_id_match.group(1)
            # Category is the prefix, e.g., aq-pack
            cat_match = re.match(r"([a-z]+-pack)", pack_id)
            if cat_match:
                category = cat_match.group(1)
                if category not in _tcg_pack_cache:
                    _tcg_pack_cache[category] = []
                _tcg_pack_cache[category].append(pack_id)

    # Only reply if all pages have been seen, or if there is only one page
    if len(_tcg_pages_seen) == total_pages or total_pages == 1:
        member = member_obj
        display_name = getattr(member, "display_name", None) or user_mention or "User"
        pretty_log(tag="debug", message=f"All pages seen. Preparing embed commands.")
        fields = []
        for category, pack_ids in _tcg_pack_cache.items():
            # Batch in groups of 20
            for i in range(0, len(pack_ids), 20):
                batch = pack_ids[i : i + 20]
                if not batch:
                    continue
                # First pack: full code, rest: only numeric suffix
                first = batch[0]
                rest = [p.split("-")[-1] for p in batch[1:]]
                cmd = f";tcg gift {user_mention} {first}"
                if rest:
                    cmd += " " + " ".join(rest)
                field_name = f"{category} ({len(batch)})"
                fields.append({"name": field_name, "value": cmd, "inline": False})

        # Discord embed limits: 25 fields per embed, 6000 chars per embed
        embeds = []
        current_fields = []
        current_length = 0
        for field in fields:
            field_length = len(field["name"]) + len(field["value"])
            # If adding this field would exceed limits, start a new embed
            if len(current_fields) >= 25 or current_length + field_length > 5900:
                embed = discord.Embed(
                    title=f"{display_name}'s TCG Gift Commands",
                    color=embed_color,
                )
                for f in current_fields:
                    embed.add_field(
                        name=f["name"], value=f["value"], inline=f["inline"]
                    )
                embeds.append(embed)
                current_fields = []
                current_length = 0
            current_fields.append(field)
            current_length += field_length
        # Add the last embed if any fields remain
        if current_fields:
            embed = discord.Embed(
                title=f"{display_name}'s TCG Gift Commands", color=embed_color
            )
            for f in current_fields:
                embed.add_field(name=f["name"], value=f["value"], inline=f["inline"])
            embeds.append(embed)

        # Send all embeds in a single message if possible, else send in batches
        # discord.py: message.reply(embeds=[...]) supports up to 10 embeds per message
        for i in range(0, len(embeds), 10):
            await message.reply(embeds=embeds[i : i + 10])

        _tcg_pack_cache.clear()
        _tcg_pages_seen.clear()
        # Optionally reset member_obj if needed
        member_obj = None

    else:
        pretty_log(
            tag="debug",
            message=f"Waiting for more pages. Current cache: {_tcg_pack_cache}",
        )
    return None
