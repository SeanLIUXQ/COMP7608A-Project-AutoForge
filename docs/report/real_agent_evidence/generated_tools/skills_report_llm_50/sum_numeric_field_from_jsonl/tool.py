import json
from typing import Union, List

def sum_numeric_field_from_jsonl(
    jsonl_text: Union[str, List[str]], field_name: str
) -> float:
    """
    Parse JSONL input (a newline-separated string or a list of JSON strings),
    extract the numeric value from ``field_name`` in each JSON object, and
    return the total sum.  Returns 0 if no valid numeric values are found.

    Args:
        jsonl_text: Either a single string containing JSON lines separated by
                    newlines, or a list where each element is a JSON string.
        field_name: The key whose numeric value should be summed.

    Returns:
        The sum of all numeric values found under ``field_name``.

    Raises:
        ValueError: If either argument is empty.
        TypeError: If ``jsonl_text`` is not a string or a list of strings.
    """
    if not isinstance(field_name, str) or not field_name:
        raise ValueError("field_name must be a non-empty string")

    if isinstance(jsonl_text, str):
        if not jsonl_text:
            raise ValueError("jsonl_text must be a non-empty string")
        lines = jsonl_text.splitlines()
    elif isinstance(jsonl_text, list):
        if not jsonl_text:
            raise ValueError("jsonl_text must be a non-empty list")
        lines = jsonl_text
    else:
        raise TypeError("jsonl_text must be a string or a list of strings")

    total = 0.0

    for line in lines:
        if not isinstance(line, str):
            continue
        line = line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(obj, dict):
            continue
        if field_name not in obj:
            continue

        value = obj[field_name]
        if value is None:
            continue
        if isinstance(value, bool):
            continue  # exclude booleans (they are int subclasses)
        if isinstance(value, (int, float)):
            total += value

    return total
