import discord
from discord import ButtonStyle
from discord.ext import commands

from config.aesthetic import Emojis
from utils.cache.cache_list import utility_cache
from utils.db.utilities_db_func import (
    fetch_user_utility,
    set_user_utility,
    update_fish_rarity,
    update_faction_ball_alert
)
from utils.essentials.safe_respond import safe_respond
from utils.logs.pretty_log import pretty_log


# 💗────────────────────────────────────────────
# [🎀 FUNCTION] Utility Settings
# 💗────────────────────────────────────────────
async def utility_settings_func(bot: commands.Bot, interaction: discord.Interaction):
    """Main entry for user utility settings."""

    user_id = interaction.user.id
    user_name = interaction.user.name

    try:
        # Fetch current settings from DB
        utility_settings = await fetch_user_utility(bot, user_id)

        # If user doesn't exist in DB, create them with defaults
        if not utility_settings:
            pretty_log(
                tag="db",
                message=f"Creating new utility settings for {user_name}",
                bot=bot,
            )

            # Save default settings to database
            await set_user_utility(
                bot,
                user_id=user_id,
                user_name=user_name,
                fish_rarity="off",
                faction_ball_alert="off",
            )

            # Set defaults for local use
            utility_settings = {
                "user_id": user_id,
                "user_name": user_name,
                "fish_rarity": "off",
                "faction_ball_alert": "off",
            }

        pretty_log(
            tag="db",
            message=f"Loaded utility settings for {user_name}: {utility_settings}",
            bot=bot,
        )

        view = UtilitySettingsView(bot, interaction.user, utility_settings)
        view.setup_initial_styles()  # Set initial button styles based on current settings

        message = await safe_respond(
            interaction, content="Modify your Utility Settings:", view=view
        )
        view.message = message  # store reference for timeout edit

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch utility settings for {user_name}: {e}",
            bot=bot,
        )
        await safe_respond(
            interaction,
            content=f"{Emojis.Pink_Error} An error occurred while fetching your utility settings. Please try again later.",
            ephemeral=True,
        )
        return


# 💗────────────────────────────────────────────
# [🌸 VIEW CLASS] utility Settings View
# 💗────────────────────────────────────────────
class UtilitySettingsView(discord.ui.View):

    def __init__(self, bot: commands.Bot, user: discord.Member, utility_settings):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.utility_settings = utility_settings
        self.message = None  # set later

    def setup_initial_styles(self):
        """Call this after the view is fully initialized to set correct initial button states."""
        self.update_button_styles()

    # 💫────────────────────────────────────
    # [🎣 BUTTON] Fish Rarity (2-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Fish Rarity: OFF", style=ButtonStyle.secondary, emoji="🎣"
    )
    async def fish_rarity_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = str(self.utility_settings.get("fish_rarity", "off")).lower()

            # Toggle state
            new_state = "off" if current_state == "on" else "on"

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} toggling Fish Rarity from {current_state} to {new_state}",
                bot=self.bot,
            )

            # Update DB and cache
            await update_fish_rarity(
                self.bot,
                user=self.user,
                fish_rarity=new_state,
            )

            self.utility_settings["fish_rarity"] = new_state
            self.update_button_styles()

            # 🔹 Display friendly text
            display_text = {
                "off": "OFF",
                "on": "ON",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Fish Rarity Settings:\n🎣 Fish Rarity set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Fish Rarity to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Fish Rarity: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Fish Rarity.",
                ephemeral=True,
            )
    # 💫────────────────────────────────────
    # [🎯 BUTTON] Faction Ball Alert (3-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(label="Faction Ball Alert: OFF", style=ButtonStyle.secondary, emoji="🎯")
    async def faction_ball_alert_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = str(
                self.utility_settings.get("faction_ball_alert", "off")
            ).lower()

            # 🔹 3-State Cycle: off → on → on_no_pings → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            else:  # on_no_pings or any other state
                new_state = "off"

            await update_faction_ball_alert(
                self.bot,
                user=self.user,
                faction_ball_alert=new_state,
            )

            self.utility_settings["faction_ball_alert"] = new_state
            self.update_button_styles()

            display_text = {
                "off": "OFF",
                "on": "ON",
                "on_no_pings": "ON (No Pings)",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Faction Ball Alert Settings:\n🎯 Faction Ball Alert set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Faction Ball Alert to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Faction Ball Alert: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Faction Ball Alert.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎨 UPDATED STYLE FUNCTION]
    # 💫────────────────────────────────────
    def update_button_styles(self):
        # 🎣 Fish Rarity Button (simple on/off)
        fish_rarity_state = str(self.utility_settings.get("fish_rarity", "off")).lower()
        fish_rarity_enable = fish_rarity_state == "on"
        self.fish_rarity_button.style = (
            ButtonStyle.success if fish_rarity_enable else ButtonStyle.secondary
        )
        self.fish_rarity_button.label = (
            f"Fish Rarity: {'ON' if fish_rarity_enable else 'OFF'}"
        )

        # 🎯 Faction Ball ALert (3 states)
        faction_ball_alert_state = str(
            self.utility_settings.get("faction_ball_alert", "off")
        ).lower()
        if faction_ball_alert_state == "off":
            self.faction_ball_alert_button.style = ButtonStyle.secondary
            self.faction_ball_alert_button.label = "Faction Ball Alert: OFF"
        elif faction_ball_alert_state == "on":
            self.faction_ball_alert_button.style = ButtonStyle.success
            self.faction_ball_alert_button.label = "Faction Ball Alert: ON"
        elif faction_ball_alert_state == "on_no_pings":
            self.faction_ball_alert_button.style = ButtonStyle.primary
            self.faction_ball_alert_button.label = "Faction Ball Alert: ON (No Pings)"
        else:
            self.faction_ball_alert_button.style = ButtonStyle.secondary
            self.faction_ball_alert_button.label = "Faction Ball Alert: OFF"
