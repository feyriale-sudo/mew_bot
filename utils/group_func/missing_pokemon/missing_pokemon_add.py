import re
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import POKEMEOW_APPLICATION_ID
from config.weakness_chart import weakness_chart
from utils.db.missing_pokemon_db_func import bulk_upsert_missing_pokemon
from utils.logs.pretty_log import pretty_log
from utils.parsers.message_link_parser import fetch_message_from_link
from utils.visuals.pretty_defer import pretty_defer, pretty_error

# 🌸──────────────────────────────────────────────
# Emoji Tags
# 🌸──────────────────────────────────────────────
REG_TAG = "<:dexcaught:667082939632189451>"
SHINY_TAG = "<:sparklesShiny:668664965095227421>"
GOLDEN_TAG = "<:dexcaughtgold:680263035952037897>"

NOT_FORM_MONS = ["tapu-fini", "tapu-koko", "tapu-lele", "tapu-bulu"]


# 🌸──────────────────────────────────────────────
# Helper to parse embed description
# 🌸──────────────────────────────────────────────
def convert_variant_dex(dex: int, prefix: str, name: str) -> int:
    """
    Convert a dex number to variant dex (Shiny/Golden) by adding leading digit.
    Example: 898 → 1898 (Shiny), 898 → 9898 (Golden)
    """
    name = name.lower()
    digits = len(str(dex))
    if prefix == "shiny":
        leading_number = "1"
        name = f"shiny {name}"

    elif prefix == "golden":
        leading_number = "9"
        name = f"golden {name}"

    if digits == 1:
        new_dex = int(f"{leading_number}00{dex}")
    elif digits == 2:
        new_dex = int(f"{leading_number}0{dex}")
    elif digits == 3:
        new_dex = int(f"{leading_number}{dex}")
    else:  # already 4 digits
        dex_str = str(dex)
        first_digit = dex_str[0]  # first character of dex as string
        if first_digit == "7":

            # Example: fetch actual dex from chart if needed
            if name in weakness_chart:
                new_dex_from_chart = weakness_chart[name]["dex"]
                if new_dex_from_chart:
                    new_dex = int(new_dex_from_chart)
                else:
                    new_dex = dex
            else:
                new_dex = dex
        else:
            new_dex = dex

    return new_dex


# 🌸──────────────────────────────────────────────
# Helper to parse embed description with Dex numbers
# 🌸──────────────────────────────────────────────
def parse_missing_pokemon_with_dex(description: str):
    """
    Parses embed description for missing Pokémon.
    Handles Shiny/Golden prefixes, Golden Mega/forms, NOT_FORM_MONS.
    Returns:
        {
            "Regular": [(dex, name), ...],
            "Shiny": [(dex, name), ...],
            "Golden": [(dex, name), ...]
        }
    Pokémon names include prefixes for Shiny/Golden, are title-cased, and duplicates removed.
    """
    missing = {"Regular": set(), "Shiny": set(), "Golden": set()}
    lines = description.splitlines()

    for idx, line in enumerate(lines, 1):
        if "`" not in line:
            continue

        # --- Extract Dex number and name ---
        match = re.search(
            r"`\s*(\d+)\s*`\s*(?:<:.+?:\d+>\s*)*(.+?)(?=\s*<:.+?:\d+>|$)", line
        )
        if not match:
            print(f"Line {idx}: Skipped → regex didn't match")
            continue

        dex_number = int(match.group(1).strip())
        pokemon_name = match.group(2).strip()
        pokemon_name = re.sub(r"<:.+?:\d+>", "", pokemon_name).strip()
        name_lower = pokemon_name.lower()

        # Tags
        has_reg = REG_TAG in line
        has_shiny = SHINY_TAG in line
        has_golden = GOLDEN_TAG in line

        # Flags
        is_shiny_prefix = name_lower.startswith("shiny ")
        is_golden_prefix = name_lower.startswith("golden ")
        is_golden_mega = name_lower.startswith("golden mega")
        is_not_form_mon = any(name_lower.endswith(mon) for mon in NOT_FORM_MONS)
        has_dash = "-" in pokemon_name and not is_not_form_mon

        # Strip prefixes for base name
        base_name = re.sub(
            r"^(shiny|golden)\s+", "", pokemon_name, flags=re.IGNORECASE
        ).title()

        # --- Handle Shiny prefix lines ---
        if is_shiny_prefix:
            if not has_reg:
                missing["Shiny"].add((dex_number, f"Shiny {base_name}"))
            continue

        # --- Handle Golden prefix lines ---
        if is_golden_prefix:
            if is_golden_mega or has_dash:
                if not has_reg:
                    missing["Regular"].add((dex_number, base_name))
                if not has_shiny:
                    shiny_dex = convert_variant_dex(dex_number, "shiny", base_name)
                    missing["Shiny"].add((shiny_dex, f"Shiny {base_name}"))
                if not has_golden:
                    golden_dex = convert_variant_dex(dex_number, "golden", base_name)
                    missing["Golden"].add((golden_dex, f"Golden {base_name}"))
            else:
                if not has_reg:
                    missing["Golden"].add((dex_number, f"Golden {base_name}"))
            continue

        # --- Normal Pokémon ---
        if not has_reg:
            missing["Regular"].add((dex_number, base_name))

        if not has_shiny:
            shiny_dex = convert_variant_dex(dex_number, "shiny", base_name)
            missing["Shiny"].add((shiny_dex, f"Shiny {base_name}"))

        if not has_golden:
            golden_dex = convert_variant_dex(dex_number, "golden", base_name)
            missing["Golden"].add((golden_dex, f"Golden {base_name}"))

    # Convert sets to sorted lists by Dex number
    final_missing = {
        k: sorted(list(v), key=lambda x: x[0]) for k, v in missing.items() if v
    }

    print("Final Missing with Dex:", final_missing)
    return final_missing


# 🌸──────────────────────────────────────────────
#  Add Missing Pokémon Function
# 🌸──────────────────────────────────────────────
async def missing_pokemon_add_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    message_link: str,
    channel: discord.TextChannel,
    role: discord.Role | None = None,
    skip: str = None,
):
    handler = await pretty_defer(
        interaction=interaction,
        content="Listing missing Pokémon...",
        ephemeral=False,
    )

    success, message, error_msg = await fetch_message_from_link(bot, message_link)
    if not success:
        return await handler.error(error_msg)

    if message.author.id != POKEMEOW_APPLICATION_ID:
        return await handler.error("This message isn't from PokéMeow. 🐾")

    if not message.embeds:
        return await handler.error("This message doesn't have an embed. 🐾")

    embed = message.embeds[0]
    if not embed.description:
        return await handler.error("This embed has no description. 🐾")

    # Parse missing Pokémon with Dex numbers
    missing = parse_missing_pokemon_with_dex(embed.description)

    if not missing:
        return await handler.success("🎉 You have all Pokémon for this page!")

    # Determine which categories to skip
    skip_map = {
        "Regular": ["Regular"],
        "Shiny": ["Shiny"],
        "Golden": ["Golden"],
        "Regular and Shiny": ["Regular", "Shiny"],
        "Regular and Golden": ["Regular", "Golden"],
        "Shiny and Golden": ["Shiny", "Golden"],
    }
    skipped_categories = skip_map.get(skip, [])

    # Build pastel pink embed
    result_embed = discord.Embed(
        title="📜 Missing Pokémon",
        description="Here’s what you’re missing! 💖",
        color=0xFFB6C1,  # Pastel pink
    )

    # Add fields with pink flair
    for category, pokemons in missing.items():
        if category in skipped_categories:
            # Show skipped notice instead of listing Pokémon
            result_embed.add_field(
                name=f"💗 {category}", value=f"Skipped ({skip})", inline=False
            )
        else:
            # Format tuples (dex, name) as "Dex • Name"
            formatted = [f"{dex:03d} • {name}" for dex, name in pokemons]
            result_embed.add_field(
                name=f"💖 {category}", value="\n".join(formatted), inline=False
            )

    # After building the embed
    view = MissingPokemonView(missing, channel, role)
    await handler.success(content="", embed=result_embed, view=view)


# 🌸──────────────────────────────────────────────
# Buttons & Modal for Missing Pokémon
# 🌸──────────────────────────────────────────────
class RemoveDexModal(discord.ui.Modal):
    def __init__(self, missing_data, message: discord.Message):
        super().__init__(title="Remove Pokémon by Dex")
        self.missing_data = missing_data
        self.message = message
        self.add_item(
            discord.ui.TextInput(
                label="Enter Dex Number to Remove",
                placeholder="e.g. 4",
                required=True,
                style=discord.TextStyle.short,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            dex_to_remove = int(self.children[0].value.strip())
        except ValueError:
            return await interaction.response.send_message(
                "❌ Invalid number entered.", ephemeral=True
            )

        removed = False
        # Remove Dex from any category it exists in
        for category in self.missing_data:
            original_len = len(self.missing_data[category])
            self.missing_data[category] = [
                (dex, name)
                for dex, name in self.missing_data[category]
                if dex != dex_to_remove
            ]
            if len(self.missing_data[category]) != original_len:
                removed = True

        if removed:
            # Refresh embed
            embed = discord.Embed(
                title="📜 Updated Missing Pokémon",
                description="Updated list after removal 💖",
                color=0xFFB6C1,
            )
            for category, pokemons in self.missing_data.items():
                if pokemons:
                    formatted = [f"{dex:03d} • {name}" for dex, name in pokemons]
                    embed.add_field(
                        name=f"💖 {category}", value="\n".join(formatted), inline=False
                    )
            await interaction.response.edit_message(embed=embed)
        else:
            await interaction.response.send_message(
                "❌ Dex not found in missing list.", ephemeral=True
            )


# ❀─────────────────────────────────────────❀
#      💖 Missing Pokémon View (Timed)
# ❀─────────────────────────────────────────❀
class MissingPokemonView(discord.ui.View):
    def __init__(
        self,
        missing_data: dict,
        channel: discord.TextChannel,
        role: discord.Role | None = None,
    ):
        super().__init__(timeout=120)  # ⏰ Auto-timeout after 2 minutes
        self.missing_data = missing_data
        self.channel = channel
        self.role = role

    # 💜────────────────────────────────────────────
    # [✅ Continue Button] • Bulk upsert to DB
    # ─────────────────────────────────────────────
    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green, emoji="✅")
    async def continue_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Upsert all missing Pokémon into the database when user clicks Continue."""
        bot = interaction.client
        user = interaction.user

        entries = []
        for category, pokemons in self.missing_data.items():
            for dex, name in pokemons:
                entries.append(
                    {
                        "user_id": user.id,
                        "user_name": user.name,
                        "dex": dex,
                        "pokemon_name": name,
                        "channel_id": self.channel.id,
                        "role_id": self.role.id if self.role else None,
                    }
                )

        if not entries:
            await interaction.response.send_message(
                "No missing Pokémon to insert into the database.", ephemeral=True
            )
            return

        await bulk_upsert_missing_pokemon(bot, entries)

        pretty_log(
            tag="💜 VIEW",
            label="UPsert Complete",
            message=f"Inserted {len(entries)} missing Pokémon for user_id={user.id} 🌸",
        )

        await interaction.response.send_message(
            f"✅ Successfully upserted {len(entries)} missing Pokémon into the database!",
            ephemeral=True,
        )

    # 💗────────────────────────────────────────────
    # [🗑️ Remove Button] • Open removal modal
    # ─────────────────────────────────────────────
    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def remove_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            RemoveDexModal(self.missing_data, interaction.message)
        )

    # 💫────────────────────────────────────────────
    # [⏳ Timeout Handler] • Disable view gracefully
    # ─────────────────────────────────────────────
    async def on_timeout(self):
        """Disable all buttons after timeout and log it."""
        for item in self.children:
            item.disabled = True
        pretty_log(
            tag="💜 VIEW",
            label="TIMEOUT",
            message="Missing Pokémon view timed out after 2 minutes ⏳",
        )

        try:
            # If message still exists, disable buttons visually
            if hasattr(self, "message") and self.message:
                await self.message.edit(view=self)
        except Exception as e:
            pretty_log("error", f"Failed to edit message on timeout: {e}")
