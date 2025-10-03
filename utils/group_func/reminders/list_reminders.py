import re
from datetime import datetime

import discord
from discord.ui import Button, View

from config.aesthetic import *
from utils.group_func.reminders.reminders_db_func import fetch_all_user_reminders
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error
from utils.parsers.reminder_parser import format_repeats_on

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
        self.message: discord.Message | None = None  # store the sent message

        # 🟣 If there's only one page, remove buttons entirely
        if self.max_page == 0:
            self.clear_items()  # <-- removes all buttons

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
        await interaction.response.edit_message(embed=(await self.get_embed()))

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
        await interaction.response.edit_message(embed=(await self.get_embed()))

    #
    async def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_reminders = self.reminders[start:end]

        embed = discord.Embed(
            title=f"⏰ {self.user.name}'s Reminders ({len(self.reminders)})",
            color=0x55AAFF,
            timestamp=datetime.now(),
        )

        for r in page_reminders:
            title = r["title"] or "No Title"
            message_snippet = (
                (r["message"][:50] + "...") if len(r["message"]) > 50 else r["message"]
            )
            remind_on_str = (
                f"- **Remind On:** <t:{int(r['remind_on'])}:F>"
                if r.get("remind_on")
                else "- **Remind On:** N/A"
            )
            repeat_str = ""
            if r.get("repeat_interval"):
                # Always use compact format for embeds
                repeat_str = f"- **Repeat Every:** {format_repeats_on(r['repeat_interval'], compact=True)}"


            # Compose field value with blockquote style
            field_value_lines = [
                f"> - **Message:** {message_snippet}",
                f"> {remind_on_str}",
            ]
            if repeat_str:
                field_value_lines.append(f"> {repeat_str}")

            # You had ping roles in old code, keep if exists
            if r.get("ping_role_1"):
                field_value_lines.append(f"> - **Ping Role 1:** <@&{r['ping_role_1']}>")
            if r.get("ping_role_2"):
                field_value_lines.append(f"> - **Ping Role 2:** <@&{r['ping_role_2']}>")

            field_value = "\n".join(field_value_lines)

            # Add a field per reminder
            embed.add_field(
                name=f"**Reminder ID: {r['user_reminder_id']} — {title}**",
                value=field_value,
                inline=False,
            )

        return await design_embed(user=self.user, embed=embed)

    async def on_timeout(self):
        """Disable all buttons when paginator times out."""
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception as e:
                pretty_log("error", f"Failed to disable paginator buttons: {e}")


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ REMINDERS LIST FUNCTION (PAGINATED)        🩷
# 🌸───────────────────────────────────────────────🌸
async def reminders_list_func(bot, interaction: discord.Interaction):
    """Display all reminders for the user in a paginated embed."""

    loader = await pretty_defer(
        interaction=interaction, content="Fetching your reminders...", ephemeral=False
    )
    reminders = await fetch_all_user_reminders(bot, interaction.user.id)

    if not reminders:
        await loader.success(content="You have no reminders set.")
        return

    # 🟣 Sort reminders by user_reminder_id (ascending)
    reminders.sort(key=lambda r: r["user_reminder_id"])

    paginator = RemindersPaginator(bot, interaction.user, reminders)
    embed = await paginator.get_embed()

    sent = await loader.success(embed=embed, view=paginator, content="")
    paginator.message = sent  # keep reference so on_timeout can edit
