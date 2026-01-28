from utils.logs.pretty_log import pretty_log

# 🌸──────────────────────────────────────────────
# Processed Message IDs Cache (Global)
# ───────────────────────────────────────────────
processed_catch_and_fish_msgs = set()
processed_egg_hatches = set()
processed_auction_prompts = set()


def clear_processed_msg_ids():
    """
    Clears the processed message IDs caches.
    """
    processed_catch_and_fish_msgs.clear()
    processed_egg_hatches.clear()
    processed_auction_prompts.clear()
    pretty_log(
        tag="cache",
        message="All processed message IDs cleared.",
    )
