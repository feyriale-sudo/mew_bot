# ─────────────────────────────────────────────
# Helper: normalize Mega Pokémon name for database/display
# ─────────────────────────────────────────────
from config.weakness_chart import weakness_chart
from utils.logs.debug_logs import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log


FORM_BASE_DEX_OFFSET = 7001
enable_debug(f"{__name__}.resolve_pokemon_input")
enable_debug(f"{__name__}.normalize_mega_input")
enable_debug(f"{__name__}.parse_special_mega_input")
enable_debug(f"{__name__}.format_mega_pokemon_name")
enable_debug(f"{__name__}.parse_form_pokemon")
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
    debug_log(f"[resolve_pokemon_input] Received input: {pokemon_input}")

    # ── Numeric Dex input ──
    if pokemon_input.isdigit():
        debug_log("[resolve_pokemon_input] Input detected as numeric Dex.")
        dex_int = int(pokemon_input)
        debug_log(f"[resolve_pokemon_input] Parsed Dex integer: {dex_int}")
        first_digit = pokemon_input[0]
        debug_log(f"[resolve_pokemon_input] First digit of input: {first_digit}")
        prefix = ""
        if first_digit == "9" and len(pokemon_input) > 3:
            debug_log("[resolve_pokemon_input] Detected Golden prefix.")
            base_dex = int(pokemon_input[1:])
            prefix = "Golden "
            debug_log(
                f"[resolve_pokemon_input] Base Dex after Golden prefix removal: {base_dex}"
            )
        elif first_digit == "1" and len(pokemon_input) > 3:
            debug_log("[resolve_pokemon_input] Detected Shiny prefix.")
            base_dex = int(pokemon_input[1:])
            prefix = "Shiny "
            debug_log(
                f"[resolve_pokemon_input] Base Dex after Shiny prefix removal: {base_dex}"
            )
        else:
            base_dex = int(pokemon_input)
            debug_log("[resolve_pokemon_input] No prefix detected.")
            debug_log(f"[resolve_pokemon_input] Base Dex: {base_dex}")

        # Lookup in weakness chart
        for name, data in weakness_chart.items():
            chart_dex = int(str(data.get("dex")).lstrip("0"))
            debug_log(
                f"[resolve_pokemon_input] Checking {name} with chart Dex {chart_dex}"
            )
            if chart_dex == base_dex:
                display_name = prefix + format_mega_pokemon_name(name)
                debug_log(
                    f"[resolve_pokemon_input] Matched Pokémon: {display_name} with Dex {base_dex}"
                )
                debug_log(
                    f"[resolve_pokemon_input] Returning: {display_name}, {dex_int}"
                )
                return display_name, dex_int

        debug_log(f"[resolve_pokemon_input] No Pokémon found with Dex #{dex_int}")
        raise ValueError(f"No Pokémon found with Dex #{dex_int}")

    # ── Name input ──
    else:
        prefix = ""
        debug_log("[resolve_pokemon_input] Input detected as Pokémon name.")
        if pokemon_input.startswith("shiny "):
            prefix = "Shiny "
            base_name = pokemon_input[6:]
            debug_log("[resolve_pokemon_input] Detected Shiny prefix.")
            debug_log(
                f"[resolve_pokemon_input] Base name after Shiny prefix removal: {base_name}"
            )
        elif pokemon_input.startswith("golden "):
            prefix = "Golden "
            base_name = pokemon_input[7:]
            debug_log("[resolve_pokemon_input] Detected Golden prefix.")
            debug_log(
                f"[resolve_pokemon_input] Base name after Golden prefix removal: {base_name}"
            )
        elif "mega" in pokemon_input:
            base_name = normalize_mega_input(pokemon_input)
            debug_log("[resolve_pokemon_input] Detected Mega form.")
            debug_log(f"[resolve_pokemon_input] Normalized Mega name: {base_name}")
        else:
            base_name = pokemon_input
            debug_log("[resolve_pokemon_input] No prefix detected.")
            debug_log(f"[resolve_pokemon_input] Base name: {base_name}")

        chart_data = weakness_chart.get(base_name)
        if not chart_data or "dex" not in chart_data:
            debug_log(f"[resolve_pokemon_input] No Pokémon found with name {base_name}")
            raise ValueError(f"No Pokémon found with name {base_name}")

        display_name = prefix + format_mega_pokemon_name(base_name)
        debug_log(f"[resolve_pokemon_input] Matched Pokémon: {display_name}")

        # Calculate Dex with offsets, but skip for 7xxx forms
        chart_dex_int = int(chart_data["dex"])
        debug_log(f"[resolve_pokemon_input] Chart Dex integer: {chart_dex_int}")
        if chart_dex_int >= 7000:
            dex_number = chart_dex_int  # already a form, skip Shiny/Golden offsets
            debug_log(
                f"[resolve_pokemon_input] Dex is a form (>=7000), using as is: {dex_number}"
            )
        else:
            if prefix == "Shiny ":
                dex_number = chart_dex_int + 1000
                debug_log("[resolve_pokemon_input] Applied Shiny Dex offset.")
            elif prefix == "Golden ":
                dex_number = chart_dex_int + 9000
                debug_log("[resolve_pokemon_input] Applied Golden Dex offset.")
            else:
                dex_number = chart_dex_int
                debug_log("[resolve_pokemon_input] No offset applied.")

        debug_log(f"[resolve_pokemon_input] Final Dex number: {dex_number}")
        if "mega" in display_name.lower():
            display_name = display_name.replace("-", " ")
            debug_log(
                f"[resolve_pokemon_input] Formatted Mega Pokémon name: {display_name}"
            )
        debug_log(
            f"[resolve_pokemon_input] Resolved Pokémon: {display_name} with Dex {dex_number}"
        )
        return display_name, dex_number


def ex_resolve_pokemon_input(pokemon_input: str):
    """
    Converts any user input (name or dex) into a normalized Pokémon name and Dex number.
    Handles:
    - Numeric Dex input (normal, shiny, golden, special forms)
    - Name input (including shiny/golden prefixes, Mega forms)
    Returns: (display_name, dex_number)
    """

    pokemon_input = pokemon_input.strip().lower()
    debug_log(f"[resolve_pokemon_input] Received input: {pokemon_input}")

    # ── Numeric Dex input ──
    if pokemon_input.isdigit():
        debug_log("[resolve_pokemon_input] Input detected as numeric Dex.")
        dex_int = int(pokemon_input)
        debug_log(f"[resolve_pokemon_input] Parsed Dex integer: {dex_int}")
        first_digit = pokemon_input[0]
        debug_log(f"[resolve_pokemon_input] First digit of input: {first_digit}")
        prefix = ""
        if first_digit == "9" and len(pokemon_input) > 3:
            debug_log("[resolve_pokemon_input] Detected Golden prefix.")
            base_dex = int(pokemon_input[1:])
            prefix = "Golden "
            debug_log(
                f"[resolve_pokemon_input] Base Dex after Golden prefix removal: {base_dex}"
            )
        elif first_digit == "1" and len(pokemon_input) > 3:
            debug_log("[resolve_pokemon_input] Detected Shiny prefix.")
            base_dex = int(pokemon_input[1:])
            prefix = "Shiny "
            debug_log(
                f"[resolve_pokemon_input] Base Dex after Shiny prefix removal: {base_dex}"
            )
        else:
            base_dex = int(pokemon_input)
            debug_log("[resolve_pokemon_input] No prefix detected.")
            debug_log(f"[resolve_pokemon_input] Base Dex: {base_dex}")

        # Lookup in weakness chart
        for name, data in weakness_chart.items():
            chart_dex = int(str(data.get("dex")).lstrip("0"))
            debug_log(
                f"[resolve_pokemon_input] Checking {name} with chart Dex {chart_dex}"
            )
            if chart_dex == base_dex:
                display_name = prefix + format_mega_pokemon_name(name)
                debug_log(
                    f"[resolve_pokemon_input] Matched Pokémon: {display_name} with Dex {base_dex}"
                )
                debug_log(
                    f"[resolve_pokemon_input] Returning: {display_name}, {dex_int}"
                )
                return display_name, dex_int

        debug_log(f"[resolve_pokemon_input] No Pokémon found with Dex #{dex_int}")
        raise ValueError(f"No Pokémon found with Dex #{dex_int}")

    # ── Name input ──
    else:
        prefix = ""
        debug_log("[resolve_pokemon_input] Input detected as Pokémon name.")
        if pokemon_input.startswith("shiny "):
            prefix = "Shiny "
            base_name = pokemon_input[6:]
            debug_log("[resolve_pokemon_input] Detected Shiny prefix.")
            debug_log(
                f"[resolve_pokemon_input] Base name after Shiny prefix removal: {base_name}"
            )
        elif pokemon_input.startswith("golden "):
            prefix = "Golden "
            base_name = pokemon_input[7:]
            debug_log("[resolve_pokemon_input] Detected Golden prefix.")
            debug_log(
                f"[resolve_pokemon_input] Base name after Golden prefix removal: {base_name}"
            )
        elif "mega" in pokemon_input:
            base_name = normalize_mega_input(pokemon_input)
            debug_log("[resolve_pokemon_input] Detected Mega form.")
            debug_log(f"[resolve_pokemon_input] Normalized Mega name: {base_name}")
        else:
            base_name = pokemon_input
            debug_log("[resolve_pokemon_input] No prefix detected.")
            debug_log(f"[resolve_pokemon_input] Base name: {base_name}")
        if "mega" in pokemon_input:
            pokemon_input = pokemon_input.replace("mega ", "mega-")
            pokemon_input = pokemon_input.lower()
        chart_data = weakness_chart.get(base_name)
        if not chart_data or "dex" not in chart_data:
            debug_log(f"[resolve_pokemon_input] No Pokémon found with name {base_name}")
            raise ValueError(f"No Pokémon found with name {base_name}")

        display_name = prefix + format_mega_pokemon_name(base_name)
        debug_log(f"[resolve_pokemon_input] Matched Pokémon: {display_name}")

        # Calculate Dex with offsets, but skip for 7xxx forms
        chart_dex_int = int(chart_data["dex"])
        debug_log(f"[resolve_pokemon_input] Chart Dex integer: {chart_dex_int}")
        if chart_dex_int >= 7000:
            dex_number = chart_dex_int  # already a form, skip Shiny/Golden offsets
            debug_log(
                f"[resolve_pokemon_input] Dex is a form (>=7000), using as is: {dex_number}"
            )
        else:
            if prefix == "Shiny ":
                dex_number = chart_dex_int + 1000
                debug_log("[resolve_pokemon_input] Applied Shiny Dex offset.")
            elif prefix == "Golden ":
                dex_number = chart_dex_int + 9000
                debug_log("[resolve_pokemon_input] Applied Golden Dex offset.")
            else:
                dex_number = chart_dex_int
                debug_log("[resolve_pokemon_input] No offset applied.")

        debug_log(f"[resolve_pokemon_input] Final Dex number: {dex_number}")
        if "mega" in display_name.lower():
            display_name = display_name.replace("-", " ")
            debug_log(
                f"[resolve_pokemon_input] Formatted Mega Pokémon name: {display_name}"
            )
        debug_log(
            f"[resolve_pokemon_input] Resolved Pokémon: {display_name} with Dex {dex_number}"
        )
        return display_name, dex_number


def normalize_mega_input(name: str) -> str:
    """Converts user input for Mega Pokémon into chart-friendly format."""
    name = name.strip().lower()
    if name.startswith("mega"):
        result = name.replace(" ", "-")  # replace all spaces
        debug_log(f"Normalized Mega input: {result}")
        return result
    debug_log(f"No normalization needed for: {name}")
    return name


def parse_special_mega_input(name: str) -> int:
    """Parses input for Pokémon, handling Shiny/Golden prefixes and Mega forms."""
    name = name.strip().lower()
    prefix = None
    debug_log(f"Parsing special Mega input: {name}")
    # Detect shiny/golden prefix
    for p in ["shiny", "golden"]:
        if name.startswith(p):
            prefix = p
            name = name[len(p) :].strip()
            break
    debug_log(f"Detected prefix: {prefix}, base name: {name}")
    # Normalize mega forms
    if name.startswith("mega"):
        name = name.replace(" ", "-")
        debug_log(f"Normalized Mega name: {name}")

    debug_log(f"Looking up dex for: {name}")

    # Lookup dex number
    dex_number = int(weakness_chart[name]["dex"])
    debug_log(f"Base dex number: {dex_number}")

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
        debug_log(f"Formatting Mega Pokémon name: {name}")
        result = name.replace("-", " ").title()
        debug_log(f"Formatted Mega Pokémon name: {result}")
        return result

    return name


def parse_form_pokemon(dex_int: int, weakness_chart: dict):
    """Returns display-friendly Pokémon name and dex using only weakness_chart."""
    debug_log(f"[parse_form_pokemon] Searching for dex_int: {dex_int}")

    # Search for an entry in weakness_chart with matching dex
    for name, data in weakness_chart.items():
        try:
            entry_dex = int(data.get("dex"))
        except (TypeError, ValueError):
            debug_log(f"[parse_form_pokemon] Skipping {name}: invalid dex value")
            continue

        if entry_dex == dex_int:
            debug_log(f"[parse_form_pokemon] Match found: {name} with dex {entry_dex}")
            # Determine variant from name prefix
            if name.lower().startswith("shiny "):
                variant_type = "shiny"
                display_name = name[6:].title()  # Remove 'shiny ' prefix
                debug_log(
                    f"[parse_form_pokemon] Variant: shiny, Display name: {display_name}"
                )
            elif name.lower().startswith("golden "):
                variant_type = "golden"
                display_name = name[7:].title()  # Remove 'golden ' prefix
                debug_log(
                    f"[parse_form_pokemon] Variant: golden, Display name: {display_name}"
                )
            else:
                variant_type = "regular"
                display_name = name.title()
                debug_log(
                    f"[parse_form_pokemon] Variant: regular, Display name: {display_name}"
                )

            debug_log(
                f"[parse_form_pokemon] Returning: {display_name}, {entry_dex}, {variant_type}"
            )
            return display_name, entry_dex, variant_type

    debug_log(f"[parse_form_pokemon] No match found for dex_int: {dex_int}")
    # If not found
    return None, None, None
