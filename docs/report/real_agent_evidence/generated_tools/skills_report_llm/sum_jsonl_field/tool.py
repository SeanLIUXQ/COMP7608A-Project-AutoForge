import json
from typing import Union, List, Dict, Any

def sum_jsonl_field(jsonl_text: Union[str, List[str]], field_name: str) -> float:
    """
    Compute the sum of a numeric field across a JSONL input.

    Args:
        jsonl_text: Either a single string containing multiple JSON lines
                    separated by newlines, or a list of strings where each
                    element is a single JSON line.
        field_name: The name of the field to sum (non-empty string).

    Returns:
        The total sum of the numeric values found for the given field.
        Values that are already int or float are summed directly.
        String values that represent valid numbers are converted (int
        preferred over float). Missing fields or non-numeric values are
        silently skipped. If no numeric values are encountered, returns 0.

    Raises:
        TypeError:  If jsonl_text is neither a string nor a list of strings,
                    or if field_name is not a non-empty string.
        json.JSONDecodeError: If any non-empty line is not valid JSON.
    """
    # Validate field_name
    if not isinstance(field_name, str) or not field_name.strip():
        raise TypeError("field_name must be a non-empty string")

    # Normalize jsonl_text to a list of lines (strings)
    if isinstance(jsonl_text, str):
        lines: List[str] = jsonl_text.splitlines()
    elif isinstance(jsonl_text, list):
        # Accept list of strings (each element is a JSON line)
        if not all(isinstance(line, str) for line in jsonl_text):
            raise TypeError("If jsonl_text is a list, every element must be a string")
        lines = jsonl_text
    else:
        raise TypeError(
            "jsonl_text must be a string (multiline JSONL) or a list of strings "
            "(each element a JSON line)"
        )

    total: float = 0.0
    for line in lines:
        line = line.strip()
        if not line:   # skip empty lines
            continue
        obj: Dict[str, Any] = json.loads(line)
        if not isinstance(obj, dict):
            # Not a JSON object; skip or treat as non-dict? plan says parsed object.
            # We'll skip if not a dict.
            continue

        # Extract value for field_name
        if field_name not in obj:
            continue

        value = obj[field_name]

        # If value is already a number, add it
        if isinstance(value, (int, float)):
            total += value
            continue

        # If value is a numeric string, attempt conversion
        if isinstance(value, str):
            value_str = value.strip()
            if not value_str:
                continue
            # Try int first, then float
            try:
                total += int(value_str)
                continue
            except ValueError:
                pass
            try:
                total += float(value_str)
                continue
            except ValueError:
                pass

        # Otherwise ignore (bool, list, None, etc.)
        continue

    # Return as int if total is whole number, else float
    if total == int(total) and not isinstance(total, bool):
        return int(total)
    return total
