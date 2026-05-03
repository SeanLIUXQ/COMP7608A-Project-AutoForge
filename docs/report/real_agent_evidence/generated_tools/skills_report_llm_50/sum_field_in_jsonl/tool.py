from typing import Iterable, Union
import json

def sum_field_in_jsonl(lines: Iterable[str], field: str) -> Union[int, float]:
    """
    Parse an iterable of JSON strings (JSONL) and return the sum of all numeric
    values found under the given field name in parsed dictionaries.

    Args:
        lines: An iterable of strings, each expected to be a single JSON object.
        field: The key whose numeric value should be summed.

    Returns:
        The sum of valid numeric values (int or float).  Returns 0 if no valid
        values are found.

    Raises:
        TypeError: If `lines` is not an iterable of strings, or `field` is not
                   a string.
    """
    if not isinstance(lines, Iterable):
        raise TypeError("lines must be an iterable of strings")
    if not isinstance(field, str):
        raise TypeError("field must be a string")

    total = 0
    for line in lines:
        if not isinstance(line, str):
            raise TypeError("Every item in lines must be a string")
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip invalid JSON lines

        # We only consider dictionaries
        if not isinstance(obj, dict):
            continue

        # Check that the field exists and its value is a plain int or float (not bool)
        value = obj.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value

    return total
