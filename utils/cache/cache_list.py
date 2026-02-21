# 🌸──────────────────────────────────────────────
#      💜 Market Alert Cache (Global) 💜
# ───────────────────────────────────────────────
market_alert_cache: list[dict] = []
# Structure
# market_alert_cache = [
#     {
#         "user_id": 123456789,
#         "pokemon": "Pikachu",
#         "dex_number": 25,
#         "max_price": 5000,
#         "notify": True,
#         "channel_id": 987654321,
#         "role_id": 192837465
#     },
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)
# Structure
# _market_alert_index = {
#     ("pikachu", 987654321): {
#         "user_id": 123456789,
#         "pokemon": "Pikachu",
#         "dex_number": 25,
#         "max_price": 5000,
#         "notify": True,
#         "channel_id": 987654321,
#         "role_id": 192837465
#     },

# 🌸──────────────────────────────────────────────
#      💜 Missing Pokémon Cache (Global) 💜
# ───────────────────────────────────────────────
missing_pokemon_cache: list[dict] = []
_missing_pokemon_index: dict[tuple[int, int], dict] = {}  # key = (user_id, dex)

# 🌸──────────────────────────────────────────────
# 💎 Market Value Cache - Global cache for market data
# ───────────────────────────────────────────────
market_value_cache: dict[str, dict] = {}

# 🌸──────────────────────────────────────────────
#       ⌚ Timer Cache (Global) ⌚
# ───────────────────────────────────────────────
timer_cache = (
    {}
)  # user_id -> {"pokemon_setting": str, "fish_setting": str, "battle_setting": str, "catchbot_setting":str, "quest_setting": str,}


# 🌸──────────────────────────────────────────────
#      👚 Utility Cache (Global) 👚
# ───────────────────────────────────────────────
utility_cache: dict[int, dict] = (
    {}
)  # user_id -> {"user_name": str, "fish_rarity": str, "faction_ball_alert":str,}

# 🌸──────────────────────────────────────────────
#      🩰 User Info Cache (Global) 🩰
# ───────────────────────────────────────────────
user_info_cache: dict[int, dict] = (
    {}
)  # user_id -> {"user_name": str, "faction": str, "patreon_tier": str, "max_quests": int, "current_quest_num": int}


# 🌸──────────────────────────────────────────────
#   🗂 Schedule Cache (Global) 🗂
# ───────────────────────────────────────────────
schedule_cache: dict[int, list[dict]] = {}  # user_id -> [schedules]
# Structure:
# schedule_cache = {
#     123456789: [  # user_id (Discord user ID)
#         {
#             "reminder_id": 1,
#             "user_id": 123456789,
#             "user_name": "Kyra Paraiso",
#             "type": "pokemon",
#             "scheduled_on": 1729123456  # Unix timestamp
#         },
#         {
#             "reminder_id": 2,
#             "user_id": 123456789,
#             "user_name": "Kyra Paraiso",
#             "type": "fish",
#             "scheduled_on": 1729127056
#         }
#     ],
#     987654321: [  # Another user
#         {
#             "reminder_id": 3,
#             "user_id": 987654321,
#             "user_name": "Another User",
#             "type": "battle",
#             "scheduled_on": 1729130000
#         }
#     ]
# }
#

# 🌸──────────────────────────────────────────────
# Daily Faction Ball Cache (Global)
# ───────────────────────────────────────────────
daily_faction_ball_cache: dict[str, str | None] = {}
# Structure:
# daily_faction_ball_cache = {
#     "aqua": "Some Value or None",
#     "flare": "Some Value or None",
#     "galactic": None,
#     "magma": "Some Value or None",
#     "plasma": None,
#     "rocket": "Some Value or None",
#     "skull": None,
#     "yell": "Some Value or None"
# }

# 🌸──────────────────────────────────────────────
#      🧸 Battle Tower Cache (Global) 🧸
# ───────────────────────────────────────────────
battle_tower_cache: dict[int, dict] = {}
# Structure
# user_id: {
# "user_name": str,
# "registered_at": int (timestamp)
# }

# 🌸──────────────────────────────────────────────
#      Auction Reminder Cache (Global) 🕰
# ───────────────────────────────────────────────
auction_reminder_cache: dict[tuple[int, int], dict] = {}
# Structure
# (ends_on (int timestamp), user_id (int)): {
#     "ends_on": int,
#     "user_id": int,
#     "user_name": str,
#     "alarm_set": bool
# }

# 🌸──────────────────────────────────────────────
#      🧩 Processed Messages🧩
# ───────────────────────────────────────────────
processed_market_feed_message_ids = set()
processed_messages_list =[
    processed_market_feed_message_ids
]