# 🎀────────────────────────────────────────────
#           🌸 Reminders Command Group 🌸
# ─────────────────────────────────────────────
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from utils.group_func.reminders import *
from utils.group_func.reminders.reminders_db_func import reminder_id_autocomplete


# 🎀────────────────────────────────────────────
#    🌸 Reminders Group Command Cog Setup 🌸
# ─────────────────────────────────────────────
class ReminderGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🎀────────────────────────────────────────────
    #           🌸 Slash Command Group 🌸
    # 🎀────────────────────────────────────────────
    reminder_group = app_commands.Group(
        name="reminder", description="Commands related to reminder"
    )

    # 🎀────────────────────────────────────────────
    #           🌸 /reminder add 🌸
    # 🎀────────────────────────────────────────────
    @reminder_group.command(name="add", description="Adds a new reminder")
    @app_commands.describe(
        message="The message for your reminder",
        remind_on="When to be reminded (Valid format: 12/30 18:20 | 12h | 1d3m)",
        title="Title for the reminder",
        ping_role_1="(Desktop) Optional role to ping",
        ping_role_2="(Desktop) Optional second role to ping",
        repeat_interval="Optional repeat interval (Valid format: 12h | 1d3m)",
        color="Optional embed color (hex, e.g., #FF00FF)",
        image_url="Optional image URL for the embed",
        thumbnail_url="Optional thumbnail URL for the embed",
        footer_text="Optional footer text for the embed",
    )
    async def add_reminder(
        self,
        interaction: discord.Interaction,
        message: str,
        remind_on: str,
        title: str,
        ping_role_1: discord.Role = None,
        ping_role_2: discord.Role = None,
        repeat_interval: str = None,
        color: str = None,
        image_url: str = None,
        thumbnail_url: str = None,
        footer_text: str = None,
    ):

        slash_cmd_name = "reminder add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=add_reminder_func,
            message=message,
            remind_on=remind_on,
            title=title,
            ping_role_1=ping_role_1,
            ping_role_2=ping_role_2,
            repeat_interval=repeat_interval,
            color=color,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            footer_text=footer_text,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /reminder remove 🌸
    # 🎀────────────────────────────────────────────
    @reminder_group.command(
        name="remove",
        description="Removes an existing reminder by ID, or all reminders",
    )
    @app_commands.autocomplete(
        reminder_id=reminder_id_autocomplete
    )  # 👈 attach autocomplete
    @app_commands.describe(reminder_id="Reminder ID, or 'all' to remove all alerts")
    async def remove_reminder(self, interaction: discord.Interaction, reminder_id: str):

        slash_cmd_name = "reminder remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=remove_reminder_func,
            reminder_id=reminder_id,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /reminder edit 🌸
    # 🎀────────────────────────────────────────────
    @reminder_group.command(name="edit", description="Updates an existing reminder")
    @app_commands.autocomplete(reminder_id=reminder_id_autocomplete)
    @app_commands.describe(
        reminder_id="The ID of the reminder to edit",
        new_message="The new message for your reminder",
        new_remind_on="When to be reminded (Valid format: 12/30 18:20 | 12h | 1d3m)",
        new_title="The new title for the reminder",
        new_ping_role_1="(Desktop) Optional new role to ping",
        new_ping_role_2="(Desktop) Optional second new role to ping",
        new_repeat_interval="Optional new repeat interval (Valid format: 12h | 1d3m)",
        new_color="Optional new embed color (hex, e.g., #FF00FF)",
        new_image_url="Optional new image URL for the embed",
        new_thumbnail_url="Optional new thumbnail URL for the embed",
        new_footer_text="Optional new footer text for the embed",
    )
    async def edit_reminder(
        self,
        interaction: discord.Interaction,
        reminder_id: str,
        new_title: str = None,
        new_message: str = None,
        new_remind_on: str = None,
        new_ping_role_1: discord.Role = None,
        new_ping_role_2: discord.Role = None,
        new_repeat_interval: str = None,
        new_color: str = None,
        new_image_url: str = None,
        new_thumbnail_url: str = None,
        new_footer_text: str = None,
    ):

        slash_cmd_name = "reminder edit"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=edit_reminder_func,
            reminder_id=reminder_id,
            new_title=new_title,
            new_message=new_message,
            new_remind_on=new_remind_on,
            new_ping_role_1=new_ping_role_1,
            new_ping_role_2=new_ping_role_2,
            new_repeat_interval=new_repeat_interval,
            new_color=new_color,
            new_image_url=new_image_url,
            new_thumbnail_url=new_thumbnail_url,
            new_footer_text=new_footer_text,
        )

    # 🎀────────────────────────────────────────────
    #           🌸 /reminder list 🌸
    # 🎀────────────────────────────────────────────
    @reminder_group.command(name="list", description="List all your active reminders")
    async def list_reminder(self, interaction: discord.Interaction):

        slash_cmd_name = "reminder list"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=reminders_list_func,
        )


# 🎀────────────────────────────────────────────
#           🌸 Cog Setup Function 🌸
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReminderGroup(bot)
    await bot.add_cog(cog)
    reminder_group = ReminderGroup.reminder_group  # top-level app_commands.Group
    # await log_command_group_full_paths_to_cache(bot=bot, group=market_alerts_group)
