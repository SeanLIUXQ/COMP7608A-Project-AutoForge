from typing import Union, List, Dict, Any

def filter_names_by_threshold(rows: List[Dict[str, Any]], threshold: Union[int, float]) -> List[str]:
    """
    Filter a list of dictionaries, keeping only rows where the 'score' value
    meets or exceeds a given threshold, and return a list of the 'name' values
    from those rows.

    Args:
        rows: A list of dictionaries. Each dictionary must contain the keys 'score'
              and 'name'.
        threshold: The numeric threshold (inclusive) that a row's 'score' must meet.

    Returns:
        A list of the 'name' strings from rows whose 'score' >= threshold.

    Raises:
        TypeError: If rows is not a list, if threshold is not a number (int/float),
                   or if any element of rows is not a dictionary.
        ValueError: If any dictionary in rows does not contain both 'score' and 'name'.
    """
    # Validate rows is a list
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")

    # Validate threshold is a number
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be an int or float")

    names = []
    for i, row in enumerate(rows):
        # Check row is a dict
        if not isinstance(row, dict):
            raise TypeError(f"Element at index {i} is not a dictionary")

        # Check required keys
        if 'score' not in row or 'name' not in row:
            raise ValueError(f"Dictionary at index {i} must contain 'score' and 'name' keys")

        # Apply threshold filter
        if row['score'] >= threshold:
            names.append(row['name'])

    return names
