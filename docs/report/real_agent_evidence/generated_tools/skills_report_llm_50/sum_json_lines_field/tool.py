import json
from typing import Iterable, Union


def sum_json_lines_field(lines: Iterable[str], field_name: str) -> Union[int, float]:
    """
    Sum the values of a specified field across a sequence of JSON lines.

    Each line is parsed as a JSON object. If the field exists and its value is
    numeric (``int`` or ``float``, *not* ``bool``), the value is added to the
    running total.  Missing fields, non‑numeric values, and malformed JSON lines
    are silently skipped.

    Args:
        lines:       An iterable of strings, where each string is a JSON object.
        field_name:  The key whose values should be summed.

    Returns:
        The total sum as an ``int`` or ``float``.  Returns 0 if no valid numeric
        values are found.

    Raises:
        TypeError: If *lines* is not an iterable of strings or *field_name* is
                   not a string.
    """
    # --- Input validation ---
    if not isinstance(field_name, str):
        raise TypeError("field_name must be a string")
    # Make sure lines is iterable (this check will fail eagerly for non‑iterables)
    try:
        iterator = iter(lines)
    except TypeError:
        raise TypeError("lines must be an iterable of strings")

    total: Union[int, float] = 0

    for line in iterator:
        if not isinstance(line, str):
            # If line is not a string, we still follow the plan's silent-skip
            # logic for malformed input; a non‑string cannot be valid JSON.
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            # Malformed JSON – skip this line
            continue

        if not isinstance(obj, dict):
            # Not a JSON object – skip
            continue

        value = obj.get(field_name)
        if value is None:
            # Field missing
            continue

        # Accept int and float but reject bool (which is a subclass of int)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        total += value

    return total
