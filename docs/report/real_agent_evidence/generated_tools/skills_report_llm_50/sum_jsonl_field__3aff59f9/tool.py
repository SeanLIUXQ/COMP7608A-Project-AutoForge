import json
from typing import Union

def sum_jsonl_field(lines: Union[str, list[str]], field: str) -> float:
    """Sum the numeric values of a field from JSONL (JSON Lines) input.

    Args:
        lines: A JSONL string (one JSON object per line) or a list of JSON strings.
        field: The key whose numeric values should be accumulated.

    Returns:
        The total sum of the field's values as an integer or float.
        Returns 0 if no valid numeric values are found.

    Raises:
        ValueError: If `field` is not a non-empty string,
                    or if `lines` is not a string or list of strings.
    """
    # Validate field
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")

    # Normalize input to list of strings
    if isinstance(lines, str):
        line_list = lines.splitlines()
    elif isinstance(lines, list) and all(isinstance(item, str) for item in lines):
        line_list = lines
    else:
        raise ValueError("lines must be a string or a list of strings")

    total = 0
    for line in line_list:
        stripped = line.strip()
        if not stripped:
            continue
        # Parse JSON
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        # Only keep JSON objects
        if not isinstance(obj, dict):
            continue
        # Retrieve field value
        value = obj.get(field)
        # Skip missing values
        if value is None:
            continue
        # Accept only int or float (exclude bool, strings, lists, etc.)
        if type(value) not in (int, float):
            continue
        total += value

    return total
