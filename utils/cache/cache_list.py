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
