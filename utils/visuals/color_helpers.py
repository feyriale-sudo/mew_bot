# 🎨───────────────────────────────────────────────🎨
#       🌈 Hex / Decimal Color → Decimal Int
# 🎨───────────────────────────────────────────────🎨
def hex_to_dec(value: str | int) -> tuple[bool, int | None, str | None]:
    """
    Convert a color value to decimal.

    Returns:
        (success, decimal_value, error_message)
        - success: bool
        - decimal_value: int if success else None
        - error_message: str if failed else None

    Accepts:
      - "#FF00AA" → 16711850
      - "FF00AA" → 16711850
      - 16711850 → 16711850
      - "16711850" → 16711850
    """
    # Case 1: Already an int
    if isinstance(value, int):
        return True, value, None

    # Case 2: Must be str
    if not isinstance(value, str):
        return False, None, f"Invalid type: {type(value)} (must be str or int)"

    value = value.strip()

    # Strip "#" if present
    if value.startswith("#"):
        value = value[1:]

    # Case 3: Looks like hex
    if all(c in "0123456789ABCDEFabcdef" for c in value):
        try:
            return True, int(value, 16), None
        except Exception:
            return False, None, f"Invalid hex string: {value}"

    # Case 4: Try as decimal string
    try:
        return True, int(value), None
    except ValueError:
        return False, None, f"Invalid color format: {value}"
