from config.aesthetic import Emojis

FISHING_COLOR = 0x87CEFA


rarity_meta = {
    "common": {
        "color": 810198,
        "emoji": Emojis.Common,
    },
    "uncommon": {
        "color": 1291495,
        "emoji": Emojis.Uncommon,
    },
    "rare": {
        "color": 16550924,
        "emoji": Emojis.Rare,
    },
    "superrare": {
        "color": 16571396,
        "emoji": Emojis.SuperRare,
    },
    "legendary": {
        "color": 10487800,
        "emoji": Emojis.Legendary,
    },
    "shiny": {
        "color": 16751052,
        "emoji": Emojis.Shiny,
    },
    "golden": {
        "color": 13939200,
        "emoji": Emojis.Golden,
    },
    "unknown": {
        "color": 0x95A5A6,
        "emoji": "❓",
    },
    "default": {"color": 0xA0D8F0},
    "event_exclusive": {"color": 15345163},
    "gigantamax": {"color": 10685254},
}

FOOTER_TEXT = {
    "caught": "Congratulations! Keep it up ✨",
    "broke_out": "Aww! Better luck next time 🩷",
    "ran_away": "Oh, no! It got away from you 💨",
}
RARE_SPAWN_COLORS = {
    "legendary": rarity_meta["legendary"]["color"],
    "shiny": rarity_meta["shiny"]["color"],
    "event_exclusive": 15345163,
}
FISHING_RARITY_TRIGGERS = ["Shiny", "Golden", "Kyogre", "Suicune"]
CONTEXT_MAP = {
    "caught": {
        "footer": FOOTER_TEXT["caught"],
        "emoji": Emojis.Catched,
    },
    "broke_out": {
        "footer": FOOTER_TEXT["broke_out"],
        "emoji": Emojis.Fled,
    },
    "ran_away": {
        "footer": FOOTER_TEXT["ran_away"],
        "emoji": Emojis.Fled,
    },
}

