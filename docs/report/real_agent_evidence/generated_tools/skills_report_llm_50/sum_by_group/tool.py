def sum_by_group(rows: list[dict], group_key: str, value_key: str) -> dict:
    """
    Sum numeric values grouped by a key from a list of dictionaries.

    Args:
        rows: list of dictionaries (can be empty).
        group_key: key to group by in each dictionary.
        value_key: key holding a numeric value to sum (defaults to 0 if missing).

    Returns:
        dict mapping group values (including None if key missing) to total summed value.

    Raises:
        TypeError: if rows is not a list, or group_key/value_key are not strings,
                   or any value encountered is not a number (int or float).
    """
    # Input validation
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(group_key, str):
        raise TypeError("group_key must be a string")
    if not isinstance(value_key, str):
        raise TypeError("value_key must be a string")

    totals = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Each row must be a dictionary")
        
        group = row.get(group_key)          # may be None
        value = row.get(value_key, 0)       # default 0 if missing
        
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Value for '{value_key}' must be numeric, got {type(value).__name__}"
            )
        
        totals[group] = totals.get(group, 0) + value

    return totals
