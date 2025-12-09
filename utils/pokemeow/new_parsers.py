from config.weakness_chart import weakness_chart
from config.weakness_chart import weakness_chart
from utils.logs.debug_logs import debug_log, enable_debug
from utils.logs.pretty_log import pretty_log


FORM_BASE_DEX_OFFSET = 7001
enable_debug(f"{__name__}.resolve_pokemon_input")

def get_name_via_dex(dex: int) -> str | None:
    """Returns the Pokémon name corresponding to the given dex number."""
    for name, data in weakness_chart.items():
        if data.get("dex") == f"{dex:04d}":
            return name
        return None


def get_dex_by_name(pokemon: str):
    """Returns the dex number corresponding to the given Pokémon name."""
    data = weakness_chart.get(pokemon.lower())
    if data:
        return data.get("dex")
    return None

def resolve_pokemon_input(pokemon_input: str):
    # Check if input is digit
    if pokemon_input.isdigit():
        dex_number = int(pokemon_input)
        pokemon_name = get_name_via_dex(dex_number)
        if not pokemon_name:
            raise ValueError(f"No Pokémon found with Dex #{dex_number}")
        debug_log(f"[resolve_pokemon_input] Resolved digit input to {pokemon_name} (Dex #{dex_number})")
        return pokemon_name, dex_number

    else:
        # If name
        if "mega " in pokemon_input:
            pokemon_input = pokemon_input.replace("mega ", "mega-")
            pokemon_input = pokemon_input.lower()

        # Get info from weakness chart
        chart_data = weakness_chart.get(pokemon_input.lower())
        if not chart_data or "dex" not in chart_data:
            debug_log(f"[resolve_pokemon_input] No Pokémon found with name {pokemon_input}")
            raise ValueError(f"No Pokémon found with name {pokemon_input}")
        dex_number = int(chart_data["dex"])
        debug_log(f"[resolve_pokemon_input] Resolved name input to {pokemon_input} (Dex #{dex_number})")
        return pokemon_input, dex_number