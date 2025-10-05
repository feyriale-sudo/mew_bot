import re
import discord

from config.aesthetic import Emojis
from utils.cache.missing_pokemon_cache import (
    find_pokemon_in_user_cache_single,
    remove_missing,
)
from utils.db.missing_pokemon_db_func import remove_missing_pokemon
from utils.logs.pretty_log import pretty_log


# 🌸──────────────────────────────────────────────
#   💖 Parse + Clean Up Multitrade Pokémon Entries
# 🌸──────────────────────────────────────────────
async def handle_multitrade_message(bot, message: discord.Message):
    """
    Extract Pokémon received by each trader from a PokéMeow multitrade embed.
    Also removes Pokémon from both DB and cache if they were previously marked as missing.

    Args:
        bot: Mew bot instance
        message (discord.Message): Message containing the PokéMeow multitrade embed.

    Returns:
        dict: { "username1": ["Pokemon1", "Pokemon2"], "username2": [...] }
    """
    if not message.embeds:
        return

    received = {}

    # 💬 Extract Pokémon per user
    for field in message.embeds[0].fields:
        name_match = re.search(r"\s(.+?)'s Pokemon", field.name)
        if not name_match:
            continue

        username_raw = name_match.group(1).strip()
        username = re.sub(r"<:.+?:\d+>\s*", "", username_raw)

        content = field.value.strip()
        if content.lower() == "none":
            received[username] = []
            continue

        pokemons = []
        for line in content.splitlines():
            line_clean = re.sub(r"<:.+?:\d+>", "", line).strip()
            name_only = re.sub(r"\s*x\d+$", "", line_clean)
            if name_only:
                pokemons.append(name_only)

        received[username] = pokemons

    # 🧩 PokéMeow multitrade logic:
    usernames = list(received.keys())
    if len(usernames) == 2:
        user1, user2 = usernames
        final_received = {
            user1: received[user2],  # user1 receives what user2 gave
            user2: received[user1],
        }
    else:
        final_received = received

    # 💫 Cleanup step — remove received Pokémon from missing cache + DB
    from utils.pokemeow.get_pokemeow_reply import get_pokemeow_reply_member

    for receiver_name, pokemons in final_received.items():
        member = await get_pokemeow_reply_member(bot, receiver_name)
        if not member or not pokemons:
            continue

        user_id = member.id
        for pokemon in pokemons:
            found = find_pokemon_in_user_cache_single(user_id, pokemon)
            if found:
                await remove_missing_pokemon(bot, user_id, pokemon)
                remove_missing(user_id, pokemon)

                pretty_log(
                    tag="💜 CACHE",
                    label="POKÉMON CLEANUP",
                    message=f"Removed '{pokemon}' from {receiver_name}'s missing list (user_id={user_id}) 🌸",
                )

    return
