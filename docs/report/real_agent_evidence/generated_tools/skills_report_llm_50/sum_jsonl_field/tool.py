import json
from typing import Iterable, Union

def sum_jsonl_field(lines: Iterable[str], field_name: str) -> Union[int, float]:
    """Sum the values of a specified field across all JSON lines in an iterable.

    Args:
        lines: An iterable of strings, each expected to be a JSON object.
        field_name: The field whose numeric values should be summed.

    Returns:
        The sum of the numeric values of the field across all valid lines.

    Raises:
        TypeError: If lines is not an iterable of strings or field_name is not a string.

    Lines that are not valid JSON, that do not contain the field, or where the
    field's value is not a number (e.g., bool, None, string, list) are skipped.
    """
    # Validate inputs
    if isinstance(lines, str):
        raise TypeError("lines must be an iterable of strings, not a string")
    if not hasattr(lines, '__iter__'):
        raise TypeError("lines must be an iterable")
    if not isinstance(field_name, str):
        raise TypeError("field_name must be a string")

    total = 0

    for line in lines:
        # Skip lines that are not strings (e.g., bytes) without raising
        if not isinstance(line, str):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue  # skip invalid JSON

        # Extract value for the given field
        value = data.get(field_name)
        if value is None:
            continue  # field missing or explicitly null

        # Only sum numbers (int, float) and reject bool (subclass of int)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value

    return total
