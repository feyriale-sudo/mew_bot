import discord
from discord import ButtonStyle
from discord.ext import commands

from config.aesthetic import Emojis
from utils.db.timers_db_func import (
    fetch_timer,
    set_timer,
)
from utils.logs.pretty_log import pretty_log
from utils.essentials.safe_respond import safe_respond


# 💗────────────────────────────────────────────
# [🎀 FUNCTION] Timer Settings
# 💗────────────────────────────────────────────
async def timer_settings_func(bot: commands.Bot, interaction: discord.Interaction):
    """Main entry for user timer settings."""

    try:
        timer_settings = await fetch_timer(bot, interaction.user.id)

        # ✅ Fallback defaults to prevent NoneType issues
        timer_settings = timer_settings or {
            "pokemon_setting": "off",
            "fish_setting": "off",
            "battle_setting": "off",
            "catchbot_setting": "off",
            "quest_setting": "off",
        }

        view = TimerSettingsView(bot, interaction.user, timer_settings)
        view.setup_initial_styles()  # Set correct initial button states

        message = await safe_respond(
            interaction, content="Modify your Timer Settings:", view=view
        )
        view.message = message  # store reference for timeout edit

        pretty_log(
            tag="ui",
            message=f"[Timer Settings] Displayed timer settings for {interaction.user.display_name}",
            bot=bot,
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to load timer settings: {e}",
            bot=bot,
        )
        await safe_respond(
            interaction,
            content="⚠️ An error occurred while loading your timer settings.",
            ephemeral=True,
        )


# 💗────────────────────────────────────────────
# [🌸 VIEW CLASS] Timer Settings View
# 💗────────────────────────────────────────────
class TimerSettingsView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user: discord.Member, timer_settings):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.timer_settings = timer_settings
        self.message = None  # set later
        # DON'T call update_button_styles() here - buttons don't exist yet!

    def setup_initial_styles(self):
        """Call this after the view is fully initialized to set correct initial button states."""
        self.update_button_styles()

    # 💫────────────────────────────────────
    # [🎯 BUTTON] Pokemon Timer (4-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Pokemon Timer: OFF", style=ButtonStyle.secondary, emoji="🎯"
    )
    async def pokemon_button(
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
                self.timer_settings.get("pokemon_setting", "off")
            ).lower()

            # 🔹 4-State Cycle: off → on → on_no_pings → react → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            elif current_state == "on_no_pings":
                new_state = "react"
            else:  # react or any other state
                new_state = "off"

            await set_timer(
                self.bot,
                user_id=self.user.id,
                user_name=self.user.display_name,
                pokemon_setting=new_state,
            )

            self.timer_settings["pokemon_setting"] = new_state
            self.update_button_styles()

            # 🔹 Display friendly text
            display_text = {
                "off": "OFF",
                "on": "ON",
                "on_no_pings": "ON (No Pings)",
                "react": "REACT",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n🎯 Pokemon Timer set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Pokemon Timer to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Pokemon Timer: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Pokemon Timer.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎣 BUTTON] Fish Timer (3-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(label="Fish Timer: OFF", style=ButtonStyle.secondary, emoji="🎣")
    async def fish_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = str(self.timer_settings.get("fish_setting", "off")).lower()

            # 🔹 3-State Cycle: off → on → on_no_pings → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            else:  # on_no_pings or any other state
                new_state = "off"

            await set_timer(
                self.bot,
                user_id=self.user.id,
                user_name=self.user.display_name,
                fish_setting=new_state,
            )

            self.timer_settings["fish_setting"] = new_state
            self.update_button_styles()

            display_text = {
                "off": "OFF",
                "on": "ON",
                "on_no_pings": "ON (No Pings)",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n🎣 Fish Timer set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Fish Timer to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Fish Timer: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Fish Timer.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [⚔️ BUTTON] Battle Timer (3-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Battle Timer: OFF", style=ButtonStyle.secondary, emoji="⚔️"
    )
    async def battle_button(
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
                self.timer_settings.get("battle_setting", "off")
            ).lower()

            # 🔹 3-State Cycle: off → on → on_no_pings → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            else:  # on_no_pings or any other state
                new_state = "off"

            await set_timer(
                self.bot,
                user_id=self.user.id,
                user_name=self.user.display_name,
                battle_setting=new_state,
            )

            self.timer_settings["battle_setting"] = new_state
            self.update_button_styles()

            display_text = {
                "off": "OFF",
                "on": "ON",
                "on_no_pings": "ON (No Pings)",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n⚔️ Battle Timer set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Battle Timer to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Battle Timer: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Battle Timer.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🤖 BUTTON] Catchbot Timer
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Catchbot Timer: OFF", style=ButtonStyle.secondary, emoji="🤖"
    )
    async def catchbot_button(
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
                self.timer_settings.get("catchbot_setting", "off")
            ).lower()
            new_state = "off" if current_state == "on" else "on"

            await set_timer(
                self.bot,
                user_id=self.user.id,
                user_name=self.user.display_name,
                catchbot_setting=new_state,
            )

            self.timer_settings["catchbot_setting"] = new_state
            self.update_button_styles()

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n🤖 Catchbot Timer set to **{'ON' if new_state == 'on' else 'OFF'}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} {'enabled' if new_state == 'on' else 'disabled'} Catchbot Timer",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Catchbot Timer: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Catchbot Timer.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [📋 BUTTON] Quest Timer
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Quest Timer: OFF", style=ButtonStyle.secondary, emoji="📋"
    )
    async def quest_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = str(self.timer_settings.get("quest_setting", "off")).lower()
            new_state = "off" if current_state == "on" else "on"

            await set_timer(
                self.bot,
                user_id=self.user.id,
                user_name=self.user.display_name,
                quest_setting=new_state,
            )

            self.timer_settings["quest_setting"] = new_state
            self.update_button_styles()

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n📋 Quest Timer set to **{'ON' if new_state == 'on' else 'OFF'}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} {'enabled' if new_state == 'on' else 'disabled'} Quest Timer",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Quest Timer: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Quest Timer.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎨 UPDATED STYLE FUNCTION]
    # 💫────────────────────────────────────
    def update_button_styles(self):
        # 🎯 Pokemon Timer Button (4 states)
        pokemon_state = str(self.timer_settings.get("pokemon_setting", "off")).lower()
        if pokemon_state == "off":
            self.pokemon_button.style = ButtonStyle.secondary
            self.pokemon_button.label = "Pokemon Timer: OFF"
        elif pokemon_state == "on":
            self.pokemon_button.style = ButtonStyle.success
            self.pokemon_button.label = "Pokemon Timer: ON"
        elif pokemon_state == "on_no_pings":
            self.pokemon_button.style = ButtonStyle.primary
            self.pokemon_button.label = "Pokemon Timer: ON (No Pings)"
        elif pokemon_state == "react":
            self.pokemon_button.style = ButtonStyle.danger
            self.pokemon_button.label = "Pokemon Timer: REACT"
        else:
            self.pokemon_button.style = ButtonStyle.secondary
            self.pokemon_button.label = "Pokemon Timer: OFF"

        # 🎣 Fish Timer Button (3 states)
        fish_state = str(self.timer_settings.get("fish_setting", "off")).lower()
        if fish_state == "off":
            self.fish_button.style = ButtonStyle.secondary
            self.fish_button.label = "Fish Timer: OFF"
        elif fish_state == "on":
            self.fish_button.style = ButtonStyle.success
            self.fish_button.label = "Fish Timer: ON"
        elif fish_state == "on_no_pings":
            self.fish_button.style = ButtonStyle.primary
            self.fish_button.label = "Fish Timer: ON (No Pings)"
        else:
            self.fish_button.style = ButtonStyle.secondary
            self.fish_button.label = "Fish Timer: OFF"

        # ⚔️ Battle Timer Button (3 states) - same as fish
        battle_state = str(self.timer_settings.get("battle_setting", "off")).lower()
        if battle_state == "off":
            self.battle_button.style = ButtonStyle.secondary
            self.battle_button.label = "Battle Timer: OFF"
        elif battle_state == "on":
            self.battle_button.style = ButtonStyle.success
            self.battle_button.label = "Battle Timer: ON"
        elif battle_state == "on_no_pings":
            self.battle_button.style = ButtonStyle.primary
            self.battle_button.label = "Battle Timer: ON (No Pings)"
        else:
            self.battle_button.style = ButtonStyle.secondary
            self.battle_button.label = "Battle Timer: OFF"

        # 🤖 Catchbot Timer Button (simple on/off)
        catchbot_state = str(self.timer_settings.get("catchbot_setting", "off")).lower()
        catchbot_enabled = catchbot_state == "on"
        self.catchbot_button.style = (
            ButtonStyle.success if catchbot_enabled else ButtonStyle.secondary
        )
        self.catchbot_button.label = (
            f"Catchbot Timer: {'ON' if catchbot_enabled else 'OFF'}"
        )

        # 📋 Quest Timer Button (simple on/off)
        quest_state = str(self.timer_settings.get("quest_setting", "off")).lower()
        quest_enabled = quest_state == "on"
        self.quest_button.style = (
            ButtonStyle.success if quest_enabled else ButtonStyle.secondary
        )
        self.quest_button.label = f"Quest Timer: {'ON' if quest_enabled else 'OFF'}"

    # 💫────────────────────────────────────
    # [⏰ TIMEOUT HANDLER]
    # 💫────────────────────────────────────
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(
                    content="⏰ Timer Settings timed out — reopen the menu to modify again.",
                    view=self,
                )
        except Exception:
            pass
