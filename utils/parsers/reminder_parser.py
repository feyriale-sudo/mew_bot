from datetime import datetime, timedelta
import re


# 🌸───────────────────────────────────────────────🌸
#         ⏰ Reminder Time String → Unix
# 🌸───────────────────────────────────────────────🌸
def parse_remind_on(value: str) -> tuple[bool, int | None, str | None]:
    """
    Convert remind_on string into Unix timestamp (seconds).

    Returns:
        (success, timestamp, error_message)
        - success: bool
        - timestamp: int (unix seconds) if success else None
        - error_message: str if failed else None

    Supports:
      - "12/30 18:20" (absolute date)
      - "1d12h", "12h30m", "30m" (relative time)

    Validates:
      - Disallows past absolute dates
      - Checks valid month/day ranges
      - Checks valid hour/minute ranges
    """
    now = datetime.now()

    # ──────────────────────────────
    # Case 1: Absolute date M/D HH:MM
    # ──────────────────────────────
    abs_date_match = re.match(r"^(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})$", value)
    if abs_date_match:
        month, day, hour, minute = map(int, abs_date_match.groups())

        if not (1 <= month <= 12):
            return False, None, f"Invalid month: {month}"
        if not (0 <= hour <= 23):
            return False, None, f"Invalid hour: {hour}"
        if not (0 <= minute <= 59):
            return False, None, f"Invalid minute: {minute}"

        try:
            target = datetime(now.year, month, day, hour, minute)
        except ValueError:
            return False, None, f"Invalid date: {month}/{day}"

        # If date already passed this year, push to next year
        if target <= now:
            target = datetime(now.year + 1, month, day, hour, minute)

        return True, int(target.timestamp()), None

    # ──────────────────────────────
    # Case 2: Relative format (XdYhZm)
    # ──────────────────────────────
    rel_pattern = re.compile(
        r"^(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?$"
    )
    rel_match = rel_pattern.match(value.strip().lower())
    if rel_match:
        days = int(rel_match.group("days") or 0)
        hours = int(rel_match.group("hours") or 0)
        minutes = int(rel_match.group("minutes") or 0)

        if days == hours == minutes == 0:
            return False, None, "Relative time must not be zero"

        delta = timedelta(days=days, hours=hours, minutes=minutes)
        target = now + delta
        return True, int(target.timestamp()), None


    # ──────────────────────────────
    # Invalid format
    # ──────────────────────────────
    return False, None, f"Invalid remind_on format: {value}"


# 🌸───────────────────────────────────────────────🌸
#         ⏰ Repeat Interval String → Seconds
# 🌸───────────────────────────────────────────────🌸
def parse_repeat_interval(value: str) -> tuple[bool, int | str]:
    """
    Convert repeat_interval string into seconds.

    Supports relative time only:
      - "1d12h", "12h30m", "30m"

    Validates:
      - No absolute dates allowed
      - Must be at least 5 minutes
      - Proper formatting (XdYhZm)

    Returns:
      - (True, seconds) if valid
      - (False, error_message) if invalid
    """
    if not isinstance(value, str) or not value.strip():
        return False, "Repeat interval must be a string"

    value = value.strip().lower()

    # Reject absolute date formats (M/D HH:MM)
    if re.match(r"^\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}$", value):
        return False, "Repeat interval cannot be an absolute date"

    # Relative time pattern
    rel_pattern = re.compile(
        r"^(?:(?P<days>\d+)d)?" r"(?:(?P<hours>\d+)h)?" r"(?:(?P<minutes>\d+)m)?$"
    )
    rel_match = rel_pattern.match(value)
    if not rel_match:
        return False, f"Invalid repeat interval format: {value}"

    days = int(rel_match.group("days") or 0)
    hours = int(rel_match.group("hours") or 0)
    minutes = int(rel_match.group("minutes") or 0)

    total_seconds = days * 86400 + hours * 3600 + minutes * 60

    # Minimum 5 minutes
    if total_seconds < 300:
        return False, "Repeat interval must be at least 5 minutes"

    return True, total_seconds
