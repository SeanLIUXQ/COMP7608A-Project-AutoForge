import json
from typing import Any, Dict, List, Union

def filter_names_by_score_threshold(
    rows: List[Dict[str, Any]], threshold: Union[int, float]
) -> List[str]:
    """
    Filter a list of records by a score threshold and return the list of names
    where score >= threshold.

    Args:
        rows: A list of dictionaries, each expected to contain at least the keys
              'name' and 'score'.
        threshold: A numeric threshold (int or float).

    Returns:
        A list of the 'name' values from rows whose 'score' is >= threshold.

    Raises:
        TypeError: If rows is not a list, threshold is not numeric, or any
                   element is not a dictionary.
        ValueError: If any dictionary is missing the 'name' or 'score' key.
    """
    # Validate rows is a list
    if not isinstance(rows, list):
        raise TypeError(f"Expected a list of dictionaries, got {type(rows).__name__}")

    # Validate threshold is numeric
    if not isinstance(threshold, (int, float)):
        raise TypeError(f"Threshold must be numeric, got {type(threshold).__name__}")

    names: List[str] = []
    for idx, row in enumerate(rows):
        # Each element must be a dictionary
        if not isinstance(row, dict):
            raise TypeError(
                f"Expected dict at index {idx}, got {type(row).__name__}"
            )
        # Must contain required keys
        if 'name' not in row:
            raise ValueError(f"Missing 'name' key in row at index {idx}")
        if 'score' not in row:
            raise ValueError(f"Missing 'score' key in row at index {idx}")

        # Filter based on score; if score cannot be compared, Python will raise
        # a TypeError automatically
        if row['score'] >= threshold:
            names.append(row['name'])

    return names
