import json
from typing import Any

def sum_json_lines_field(lines: list[str], field: str) -> float:
    """Sum numeric values of a given field from a list of JSON strings.

    Args:
        lines: A list of JSON-formatted strings.
        field: The key whose numeric value should be summed.

    Returns:
        The total sum as a float. Invalid JSON lines, missing fields,
        and non-numeric values are silently skipped. Returns 0.0 for
        an empty list.
    
    Raises:
        TypeError: If lines is not a list or field is not a string.
    """
    if not isinstance(lines, list):
        raise TypeError("lines must be a list of strings.")
    if not isinstance(field, str):
        raise TypeError("field must be a string.")

    total = 0.0
    for line in lines:
        # skip non-string entries gracefully
        if not isinstance(line, str):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        # only operate on object dicts
        if not isinstance(data, dict):
            continue
        if field not in data:
            continue
        value = data[field]
        # attempt numeric conversion; skip on failure
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue
        total += num
    return total
