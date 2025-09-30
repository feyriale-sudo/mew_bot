# ─────────────────────────────────────────────
# Helper: normalize Mega Pokémon name for database/display
# ─────────────────────────────────────────────
from config.weakness_chart import weakness_chart
from utils.logs.pretty_log import pretty_log

FORM_BASE_DEX_OFFSET = 7001


# ─────────────────────────────────────────────
# Helper: Resolve Pokémon Name and Dex
# ─────────────────────────────────────────────
def resolve_pokemon_input(pokemon_input: str):
    """
    Converts any user input (name or dex) into a normalized Pokémon name and Dex number.
    Handles:
    - Numeric Dex input (normal, shiny, golden, special forms)
    - Name input (including shiny/golden prefixes, Mega forms)
    Returns: (display_name, dex_number)
    """
    
    pokemon_input = pokemon_input.strip().lower()

    # ── Numeric Dex input ──
    if pokemon_input.isdigit():
        dex_int = int(pokemon_input)

        first_digit = pokemon_input[0]
        prefix = ""
        if first_digit == "9" and len(pokemon_input) > 3:
            base_dex = int(pokemon_input[1:])
            prefix = "Golden "
        elif first_digit == "1" and len(pokemon_input) > 3:
            base_dex = int(pokemon_input[1:])
            prefix = "Shiny "
        else:
            base_dex = int(pokemon_input)

        # Lookup in weakness chart
        for name, data in weakness_chart.items():
            chart_dex = int(str(data.get("dex")).lstrip("0"))
            if chart_dex == base_dex:
                display_name = prefix + format_mega_pokemon_name(name)

                return display_name, dex_int

        raise ValueError(f"No Pokémon found with Dex #{dex_int}")

    # ── Name input ──
    else:
        prefix = ""
        if pokemon_input.startswith("shiny "):
            prefix = "Shiny "
            base_name = pokemon_input[6:]
        elif pokemon_input.startswith("golden "):
            prefix = "Golden "
            base_name = pokemon_input[7:]
        else:
            base_name = normalize_mega_input(pokemon_input)

        chart_data = weakness_chart.get(base_name)
        if not chart_data or "dex" not in chart_data:

            raise ValueError(f"No Pokémon found with name {base_name}")

        display_name = prefix + format_mega_pokemon_name(base_name)

        #
        # Calculate Dex with offsets, but skip for 7xxx forms
        chart_dex_int = int(chart_data["dex"])
        if chart_dex_int >= 7000:
            dex_number = chart_dex_int  # already a form, skip Shiny/Golden offsets

        else:
            if prefix == "Shiny ":
                dex_number = chart_dex_int + 1000
            elif prefix == "Golden ":
                dex_number = chart_dex_int + 9000
            else:
                dex_number = chart_dex_int

        return display_name, dex_number


def normalize_mega_input(name: str) -> str:
    """Converts user input for Mega Pokémon into chart-friendly format."""
    name = name.strip().lower()
    if name.startswith("mega"):
        result = name.replace(" ", "-")  # replace all spaces
        return result
    return name


def parse_special_mega_input(name: str) -> int:
    """Parses input for Pokémon, handling Shiny/Golden prefixes and Mega forms."""
    name = name.strip().lower()
    prefix = None

    # Detect shiny/golden prefix
    for p in ["shiny", "golden"]:
        if name.startswith(p):
            prefix = p
            name = name[len(p) :].strip()
            break

    # Normalize mega forms
    if name.startswith("mega"):
        name = name.replace(" ", "-")

    # Lookup dex number
    dex_number = int(weakness_chart[name]["dex"])

    # Apply shiny/golden offset
    if prefix == "shiny":
        final_dex = dex_number + 1
    elif prefix == "golden":
        final_dex = dex_number + 2
    else:
        final_dex = dex_number

    return final_dex


def format_mega_pokemon_name(name: str) -> str:
    """Replace hyphen with space and title-case Mega forms."""
    if name.lower().startswith("mega-") or name.lower().startswith("mega "):
        result = name.replace("-", " ").title()
        return result

    return name


def parse_form_pokemon(dex_int: int, weakness_chart: dict):
    """Returns display-friendly Pokémon name and dex using only weakness_chart."""

    # Search for an entry in weakness_chart with matching dex
    for name, data in weakness_chart.items():
        try:
            entry_dex = int(data.get("dex"))
        except (TypeError, ValueError):
            continue

        if entry_dex == dex_int:
            # Determine variant from name prefix
            if name.lower().startswith("shiny "):
                variant_type = "shiny"
                display_name = name[6:].title()  # Remove 'shiny ' prefix
            elif name.lower().startswith("golden "):
                variant_type = "golden"
                display_name = name[7:].title()  # Remove 'golden ' prefix
            else:
                variant_type = "regular"
                display_name = name.title()

            return display_name, entry_dex, variant_type

    # If not found
    return None, None, None
