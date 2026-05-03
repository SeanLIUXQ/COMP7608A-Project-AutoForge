import json
from typing import Any, Union

def sum_jsonl_field(lines: list[str], field_name: str) -> Union[int, float]:
    """
    Parse a list of JSON strings and sum the numeric values of a given field.

    Args:
        lines: A list of strings, each containing a JSON object (or empty/invalid).
        field_name: The name of the JSON field whose values should be summed.

    Returns:
        The total sum of all numeric values found for the specified field.
        Returns 0 if no valid numeric values are present.

    Raises:
        TypeError: If `lines` is not a list or `field_name` is not a non-empty string.
    """
    if not isinstance(lines, list):
        raise TypeError("lines must be a list")
    if not isinstance(field_name, str) or field_name == "":
        raise ValueError("field_name must be a non-empty string")

    total: Union[int, float] = 0
    for entry in lines:
        # Skip non-string entries gracefully
        if not isinstance(entry, str):
            continue
        stripped = entry.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        # Only dict-like objects are considered for field extraction
        if not isinstance(obj, dict):
            continue
        value = obj.get(field_name)
        # Accept numbers but reject booleans (which are ints in Python)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value
    return total
