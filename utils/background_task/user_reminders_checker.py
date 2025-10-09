import asyncio
import re
from datetime import datetime, timedelta

import discord
from discord.ui import Button, View

from config.aesthetic import *
from config.settings import Channels
from utils.group_func.reminders.reminders_db_func import (
    fetch_due_reminders,
    remove_user_reminder,
    update_user_reminder,
)
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error

REMINDER_CHANNEL_ID = Channels.reminders


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PROCESS DUE REMINDERS LOOP FUNCTION        🩷
# 🌸───────────────────────────────────────────────🌸
async def process_due_reminders(bot):
    """Check due reminders and send them to the reminder channel.
    Repeats reminders if repeat_interval is set, otherwise deletes them.
    """
    try:
        # Add timeout protection for the entire function
        async with asyncio.timeout(60):  # 60 second timeout

            reminders = await fetch_due_reminders(bot)

            if not reminders:
                return  # nothing to process

            reminder_channel = bot.get_channel(REMINDER_CHANNEL_ID)
            if not reminder_channel:
                pretty_log(
                    tag="error",
                    message=f"Reminder channel {REMINDER_CHANNEL_ID} not found",
                )
                return

            successful_reminders = 0
            failed_reminders = 0

            for i, r in enumerate(reminders):
                try:
                    pretty_log(
                        "debug",
                        f"Processing reminder {i+1}/{len(reminders)}: ID {r.get('user_reminder_id')}",
                    )

                    # 📝 Make sure remind_on is a datetime (convert if stored as Unix int)
                    remind_on = (
                        datetime.fromtimestamp(r["remind_on"])
                        if isinstance(r["remind_on"], (int, float))
                        else r["remind_on"]
                    )

                    # Build the embed for the reminder
                    embed = discord.Embed(
                        title=r["title"] or "Reminder",
                        description=r["message"],
                        color=r["color"] or 0xFF66A3,
                        timestamp=datetime.now(),
                    )
                    if r.get("image_url"):
                        embed.set_image(url=r["image_url"])
                    if r.get("thumbnail_url"):
                        embed.set_thumbnail(url=r["thumbnail_url"])
                    if r.get("footer_text"):
                        guild_icon_url = (
                            reminder_channel.guild.icon.url
                            if reminder_channel.guild.icon
                            else None
                        )
                        embed.set_footer(text=r["footer_text"], icon_url=guild_icon_url)

                    # Prepare ping roles if any
                    ping_text = ""
                    if r.get("ping_role_1"):
                        ping_text += f"<@&{r['ping_role_1']}> "
                    if r.get("ping_role_2"):
                        ping_text += f"<@&{r['ping_role_2']}> "

                    # 📤 Send the reminder with timeout protection
                    try:
                        async with asyncio.timeout(
                            10
                        ):  # 10 second timeout for Discord send
                            await reminder_channel.send(
                                content=ping_text or None, embed=embed
                            )
                            pretty_log(
                                "debug",
                                f"Successfully sent reminder {r.get('user_reminder_id')}",
                            )
                    except asyncio.TimeoutError:
                        pretty_log(
                            "warn",
                            f"Timeout sending reminder {r.get('user_reminder_id')} - Discord API slow",
                        )
                        failed_reminders += 1
                        continue
                    except discord.HTTPException as e:
                        if e.status == 503:
                            pretty_log(
                                "warn",
                                f"Discord API unavailable (503) for reminder {r.get('user_reminder_id')}",
                            )
                            failed_reminders += 1
                            continue
                        else:
                            raise

                    # 🔁 Handle repeat vs one-off with timeout protection
                    try:
                        async with asyncio.timeout(
                            5
                        ):  # 5 second timeout for DB operations
                            if r.get("repeat_interval"):
                                # If remind_on is datetime → convert to unix int before adding
                                if isinstance(remind_on, datetime):
                                    new_remind_on = int(remind_on.timestamp()) + int(
                                        r["repeat_interval"]
                                    )
                                else:
                                    # Already unix int
                                    new_remind_on = int(remind_on) + int(
                                        r["repeat_interval"]
                                    )

                                await update_user_reminder(
                                    bot,
                                    r["user_id"],
                                    r["user_reminder_id"],
                                    {"remind_on": new_remind_on},  # always int
                                )
                                pretty_log(
                                    tag="success",
                                    message=(
                                        f"🔁 Repeated reminder {r['user_reminder_id']} for user {r['user_id']}, "
                                        f"next at <t:{new_remind_on}:F>"
                                    ),
                                )
                            else:
                                await remove_user_reminder(
                                    bot, r["user_id"], r["user_reminder_id"]
                                )
                                pretty_log(
                                    tag="success",
                                    message=(
                                        f"🗑️ One-off reminder {r['user_reminder_id']} sent and deleted "
                                        f"for user {r['user_id']}"
                                    ),
                                )
                    except asyncio.TimeoutError:
                        pretty_log(
                            "warn",
                            f"Timeout updating/removing reminder {r.get('user_reminder_id')} - database slow",
                        )
                        failed_reminders += 1
                        continue

                    successful_reminders += 1

                except Exception as e:
                    failed_reminders += 1
                    pretty_log(
                        tag="error",
                        message=(
                            f"Failed to send/process reminder {r.get('user_reminder_id')} "
                            f"for user {r.get('user_id')}: {e}"
                        ),
                        include_trace=True,
                    )
                    # Continue processing other reminders instead of stopping

            pretty_log(
                "info",
                f"Reminder batch complete: {successful_reminders} successful, {failed_reminders} failed",
            )

    except asyncio.TimeoutError:
        pretty_log(
            "error",
            "Reminder processing timed out after 60 seconds - this indicates a serious issue",
        )
    except Exception as e:
        pretty_log(
            "error", f"Critical error in reminder processing: {e}", include_trace=True
        )
