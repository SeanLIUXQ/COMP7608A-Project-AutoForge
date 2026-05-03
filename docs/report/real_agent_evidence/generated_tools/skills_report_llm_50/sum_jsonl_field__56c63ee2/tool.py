import json
from typing import Union, List

def sum_jsonl_field(input_data: Union[str, List[str]], field: str) -> Union[int, float]:
    """
    Sum all numeric values found under a given field across JSONL data.

    Args:
        input_data: A JSONL string (multiline) or a list of JSON strings.
        field: The key whose numeric values should be summed.

    Returns:
        The total sum (int if all values are integers, float if any float).
        Returns 0 if no valid numeric entries are found.

    Raises:
        TypeError: If input_data is not a str or list of str.
        ValueError: If field is not a non-empty string.
    """
    # Validate input type
    if not isinstance(input_data, (str, list)):
        raise TypeError("input_data must be a str or a list of str")
    if isinstance(input_data, list):
        if not all(isinstance(item, str) for item in input_data):
            raise TypeError("All items in input_data list must be strings")
    if not isinstance(field, str) or field == "":
        raise ValueError("field must be a non-empty string")

    # Normalize to list of lines
    if isinstance(input_data, str):
        lines = input_data.splitlines()
    else:
        lines = input_data

    total: Union[int, float] = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        value = obj.get(field)
        if value is None:
            continue
        # Accept only numeric types, excluding booleans (which are a subclass of int)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value
    return total
