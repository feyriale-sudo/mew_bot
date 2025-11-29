def format_display_pokemon_name(name: str) -> str:
    """
    Removes dashes from a Pokémon's name and returns it in title case.
    Example: 'mega-diancie' -> 'Mega Diancie'
    """
    return name.replace("-", " ").title()
