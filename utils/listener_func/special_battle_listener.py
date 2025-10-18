import time

import discord

from utils.db.special_battle_timer_db import (
    upsert_special_battle_timer,
)
from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member
from utils.logs.pretty_log import pretty_log
from config.aesthetic import Emojis
BATTLE_TIMER = 30 * 60  # 30 minutes in seconds


# 🍭 Listener for special battle NPC timers
async def special_battle_npc_listener(bot: discord.Client, message: discord.Message):

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    user_id = member.id
    user_name = str(member)

    channel_id = message.channel.id
    npc_name = "irida"

    # Ends on timestamp = now + BATTLE_TIMER
    ends_on = int(time.time()) + BATTLE_TIMER

    # Upsert the special battle timer
    await upsert_special_battle_timer(
        bot, user_id, user_name, npc_name, ends_on, channel_id
    )
    await message.reference.resolved.add_reaction(Emojis.sched_react)
