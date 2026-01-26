import re
from typing import List

import discord
from discord.ui import Button, View

from utils.cache.cache_list import auction_reminder_cache
from utils.db.auction_reminder_db import (
    delete_all_auction_reminders,
    update_auction_reminder_alarm,
    upsert_auction_reminder,
)
from utils.logs.pretty_log import pretty_log
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

# Put in on message listener later
class Reminders_Buttons(View):
    def __init__(self, bot, member: discord.Member, ends_on: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.bot = bot
        self.member = member
        self.ends_on = ends_on
        self.message: discord.Message | None = None  # store the sent message

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This is not your button.", ephemeral=True
            )
            return
        # Update alarm_set to True in DB and cache
        await update_auction_reminder_alarm(self.bot, self.ends_on, True)
        await interaction.response.edit_message(
            content="✅ Auction reminder alarm has been set!", view=None
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This is not your button.", ephemeral=True
            )
            return
        # DO nothing and just send a don't forget to set reminder message
        await interaction.response.edit_message(
            content="⚠️ Don't forget to set an auction reminder later!", view=None
        )

    async def on_timeout(self):
        # Disable buttons on timeout
        for item in self.children:
            item.disabled = True


async def send_reminder_prompt_embed(
    bot: discord.Client,
    member: discord.Member,
    channel: discord.TextChannel,
):
    """
    Sends an embed prompt to the user asking if they want to set an auction reminder.
    """
    embed = discord.Embed(
        title="Auction Reminder",
        description=(
            f"Have you set an alarm for the auction that will end on <t:{member.id}:f>?"
        ),
        # Pastel pink
        color=0xFFB6C1,
    )
    view = Reminders_Buttons(bot, member, member.id)
    sent_msg = await channel.send(content=member.mention, embed=embed, view=view)
    view.message = sent_msg


async def auction_command_listener(
    bot, before_message: discord.Message, message: discord.Message
):
    """
    Listens for auction-related commands in messages and processes them.
    """

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    embed_description = embed.description if embed.description else ""

    # Get Member
    member = await get_pokemeow_reply_member(before_message)
    if not member:
        pretty_log(
            tag="info",
            message=f"Could not find member for auction command listener in message ID {message.id}",
        )
        return
    embed_description_lower = embed_description.lower()
    if "there are no auctions active" in embed_description_lower:
        # Process no auctions
        await process_no_auctions(bot, message)
        return
    else:
        # Process auction timestamps
        await process_auction_timestamps(bot, member, message)
        return


def extract_unique_auction_end_timestamps(embed_description: str) -> List[int]:
    """
    Extracts unique auction end timestamps from the embed description.
    Only timestamps after 'Ends <t:...:R>' are returned. Ignores 'Bid placed <t:...:R>'.
    Returns a list of unique integer timestamps.
    """
    # Regex to match 'Ends <t:TIMESTAMP:R>'
    ends_pattern = re.compile(r"Ends <t:(\d+):R>")
    timestamps = set(int(match) for match in ends_pattern.findall(embed_description))
    return list(timestamps)


async def process_auction_timestamps(
    bot, member: discord.Member, message: discord.Message
):
    """
    Processes auction end timestamps from a message and updates the auction reminder cache and database.
    """
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    embed_description = embed.description if embed.description else ""
    timestamp_list = extract_unique_auction_end_timestamps(embed_description)
    if not timestamp_list:
        return
    from utils.cache.auction_reminder_cache import (
        is_timestamp_more_than_5_hours_away_cache,
    )

    for ends_on in timestamp_list:
        # Check if already in cache
        if ends_on not in auction_reminder_cache:
            # Not in cache, insert new reminder with alarm_set=False
            if not is_timestamp_more_than_5_hours_away_cache(ends_on):
                continue  # Skip if less than 5 hours away

            await upsert_auction_reminder(bot, ends_on, alarm_set=False)
            await send_reminder_prompt_embed(bot, member, message.channel)
        else:
            # Check if alarm_set is False and update if necessary
            alarm_set = auction_reminder_cache[ends_on]
            if not alarm_set:
                await send_reminder_prompt_embed(bot, member, message.channel)
            else:
                # Skip if alreday true
                continue
    pretty_log(
        tag="info",
        message=(
            f"Processed auction reminders for member ID {member.id} "
            f"with timestamps: {timestamp_list}"
        ),
    )


async def process_no_auctions(bot, message: discord.Message):
    """
    Processes messages indicating no ongoing auctions and clears related reminders.
    """
    # Check if there is auction reminder cache
    if not auction_reminder_cache:
        return

    # Remove all auction reminders from DB and cache
    await delete_all_auction_reminders(bot)
    pretty_log(
        tag="info",
        message=(
            f"Cleared all auction reminders due to no ongoing auctions message "
            f"in message ID {message.id}"
        ),
    )
    return
