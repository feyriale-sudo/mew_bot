# 🌸──────────────────────────────────────────────
#      💜 Market Alert Cache (Global) 💜
# ───────────────────────────────────────────────
market_alert_cache: list[dict] = []
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)

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
)  # user_id -> {"pokemon_setting": str, "fish_setting": str, "battle_setting": str}

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
