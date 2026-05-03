import json
from typing import Iterable, Union, Any

def sum_jsonl_field(lines: Iterable[str], field: str) -> float:
    """
    Sum the numeric values of a specified field across a sequence of JSON Lines.

    Each input string is parsed as a JSON object. Lines that are not valid JSON,
    do not contain the given field, or have a non-numeric value for the field
    are silently skipped.

    Args:
        lines: An iterable of strings, each expected to be a JSON object (JSONL).
        field: The key whose numeric value should be summed.

    Returns:
        The total sum as a float. Returns 0.0 if no valid numeric values are found.

    Raises:
        TypeError: If `lines` is not an iterable of strings.
    """
    # Validate that lines is an iterable of strings (fail fast on invalid input)
    try:
        iterator = iter(lines)
    except TypeError:
        raise TypeError("lines must be an iterable") from None

    total = 0.0
    for line in iterator:
        if not isinstance(line, str):
            raise TypeError("All items in `lines` must be strings")

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed JSON

        if not isinstance(obj, dict):
            continue  # skip non-object JSON values (arrays, strings, etc.)

        if field not in obj:
            continue  # field missing

        value = obj[field]
        # Accept only numeric types, excluding booleans (which are a subclass of int)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        total += value

    return total
