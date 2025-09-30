import re
from datetime import datetime

import discord
from discord.ui import Button, View

from config.aesthetic import *
from utils.group_func.reminders.reminders_db_func import fetch_all_user_reminders
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PAGINATED REMINDERS LIST FUNCTION          🩷
# 🌸───────────────────────────────────────────────🌸
class RemindersPaginator(View):
    def __init__(self, bot, user, reminders, per_page=10, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.reminders = reminders
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(reminders) - 1) // per_page

        # Disable buttons if only 1 page
        self.prev_button.disabled = self.next_button.disabled = self.max_page == 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page -= 1
        if self.page < 0:
            self.page = self.max_page
        await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page += 1
        if self.page > self.max_page:
            self.page = 0
        await interaction.response.edit_message(embed=self.get_embed())

    def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_reminders = self.reminders[start:end]

        desc = ""
        for r in page_reminders:
            title = r["title"] or "No Title"
            message_snippet = (
                (r["message"][:50] + "...") if len(r["message"]) > 50 else r["message"]
            )
            remind_on_str = (
                f"<t:{int(r['remind_on'].timestamp())}:F>"
                if r.get("remind_on")
                else "N/A"
            )
            repeat_str = (
                f" | Repeat: {r['repeat_interval']}s"
                if r.get("repeat_interval")
                else ""
            )
            ping_roles = ""
            if r.get("ping_role_1"):
                ping_roles += f" | <@&{r['ping_role_1']}>"
            if r.get("ping_role_2"):
                ping_roles += f" | <@&{r['ping_role_2']}>"

            desc += f"**{r['reminder_id']}: {title}** — {message_snippet} — {remind_on_str}{repeat_str}{ping_roles}\n"

        embed = discord.Embed(
            title=f"⏰ {self.user.name}'s Reminders ({len(self.reminders)})",
            description=desc,
            color=0x55AAFF,
            timestamp=datetime.now(),
        )
        return design_embed(user=self.user, embed=embed)


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ REMINDERS LIST FUNCTION (PAGINATED)        🩷
# 🌸───────────────────────────────────────────────🌸
async def reminders_list_func(bot, interaction: discord.Interaction):
    """Display all reminders for the user in a paginated embed."""

    loader = await pretty_defer(
        interaction, "Fetching your reminders...", ephemeral=False
    )
    reminders = await fetch_all_user_reminders(bot, interaction.user.id)

    if not reminders:
        await loader.error(content="You have no reminders set.")
        return

    paginator = RemindersPaginator(bot, interaction.user, reminders)
    await loader.success(embed=paginator.get_embed(), view=paginator)
