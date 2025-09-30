# Global cache list & index
market_alert_cache: list[dict] = []
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)
