def filter_names_by_score(rows: list[dict], threshold: float) -> list[str]:
    """
    Return a list of 'name' values from rows whose 'score' is at least the threshold.

    Args:
        rows: A list of dictionaries, each containing the keys 'score' and 'name'.
        threshold: The minimum score value (inclusive) for a row to be included.

    Returns:
        A list of the 'name' strings from the matching rows.

    Raises:
        TypeError: If rows is not a list of dicts or threshold is not numeric.
        ValueError: If any row lacks the required keys 'score' or 'name'.
    """
    # Validate rows is a list
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries")
    # Validate threshold is a real number (and not a boolean)
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise TypeError("threshold must be a numeric value (int or float)")

    names = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"rows[{i}] must be a dictionary")
        missing = [key for key in ('score', 'name') if key not in row]
        if missing:
            raise ValueError(f"rows[{i}] is missing required key(s): {missing}")
        if row['score'] >= threshold:
            names.append(row['name'])
    return names
