import json
from typing import Iterable, Union

def sum_jsonl_field(jsonl_text, field_name: str) -> Union[int, float]:
    """
    Parse a string of JSON lines (or an iterable of such lines) and return
    the sum of the numeric values for `field_name` across all valid JSON objects.

    Args:
        jsonl_text: A str containing one JSON value per line, or an iterable
                    of such strings.
        field_name: The key whose numeric values should be summed.

    Returns:
        The total sum as an int or float.  Returns 0 if no valid entries are found.

    Raises:
        ValueError: If `field_name` is not a non‑empty string.
        TypeError: If `jsonl_text` is neither a str nor an iterable of strings.
    """
    # Validate field_name
    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("field_name must be a non-empty string")

    # Handle input: single string -> lines; otherwise treat as iterable of lines
    if isinstance(jsonl_text, str):
        lines = jsonl_text.splitlines()
    else:
        try:
            lines = iter(jsonl_text)
        except TypeError:
            raise TypeError("jsonl_text must be a string or an iterable of strings")

    total = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse JSON; skip malformed lines
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Must be a dict containing the field
        if not isinstance(obj, dict) or field_name not in obj:
            continue

        value = obj[field_name]
        # Accept only true numbers (bool is a subclass of int, exclude it)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value

    return total
