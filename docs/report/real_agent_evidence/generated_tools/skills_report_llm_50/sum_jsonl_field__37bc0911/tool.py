import json
from typing import Iterable, Union


def sum_jsonl_field(lines: Iterable[str], field: str) -> float:
    """
    Parse a sequence of JSONL (JSON lines) strings and return the sum of the
    numeric values found under the given field name.

    Lines that are not valid JSON, do not represent a JSON object, or where
    the requested field is missing or holds a non‑numeric (or boolean) value
    are silently skipped.

    Args:
        lines: An iterable of strings, each expected to be a JSON object.
        field: The name of the field whose numeric value should be summed.

    Returns:
        The sum of all valid numeric field values as a float.
        If no valid values are encountered, 0.0 is returned.

    Raises:
        TypeError: If *field* is not a string.
    """
    if not isinstance(field, str):
        raise TypeError("field must be a string")

    total: float = 0.0

    for line in lines:
        # Parse the line, skip if not valid JSON
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue

        # Only JSON objects (dicts) are considered
        if not isinstance(obj, dict):
            continue

        # Missing field -> skip
        if field not in obj:
            continue

        value = obj[field]

        # Accept only true numeric values (int or float), excluding bools
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value

    return total
