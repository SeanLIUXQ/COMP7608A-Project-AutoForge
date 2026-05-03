import json
from typing import Any

def sum_jsonl_field(lines: list[str], field: str) -> float:
    """
    Parse a list of JSON lines and return the sum of a numeric field.

    Args:
        lines: A list of strings, each containing a valid JSON object (or not).
        field: The JSON key whose numeric values should be summed.

    Returns:
        The sum of all valid numeric values for the given field across all lines.
        Lines that cannot be parsed as JSON or whose field value is missing or
        non-numeric (including boolean) are silently skipped.

    Raises:
        TypeError: If `lines` is not a list of strings or `field` is not a string.
    """
    # Validate input types
    if not isinstance(lines, list):
        raise TypeError("lines must be a list")
    if not all(isinstance(line, str) for line in lines):
        raise TypeError("All elements in lines must be strings")
    if not isinstance(field, str):
        raise TypeError("field must be a string")

    total: float = 0.0

    for line in lines:
        try:
            obj: Any = json.loads(line)
        except json.JSONDecodeError:
            continue   # not valid JSON, skip this line

        # The plan says "if the field value is a number, add it"
        if field in obj:
            val = obj[field]
            # Accept int and float, but not bool (which is a subclass of int in Python)
            if isinstance(val, (int, float)) and type(val) is not bool:
                total += val

    return total
