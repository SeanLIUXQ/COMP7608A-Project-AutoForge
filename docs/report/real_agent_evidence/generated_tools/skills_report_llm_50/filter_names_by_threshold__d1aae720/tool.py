def filter_names_by_threshold(rows: list[dict], threshold: float, score_field: str = "score", name_field: str = "name") -> list:
    """
    Filter a list of rows (dictionaries) by a score threshold and return the
    corresponding names.

    For each row, the value under `score_field` is compared to `threshold`.
    Rows where the field is missing or the value is non-numeric are silently
    skipped. If the score is >= `threshold`, the value under `name_field` is
    appended to the result (it can be of any type, including None if the key
    is absent).

    Args:
        rows: A list of dictionaries to filter.
        threshold: The minimum numeric score to keep.
        score_field: Key to look up the numeric score in each row (default "score").
        name_field: Key to look up the name in each row (default "name").

    Returns:
        A list of name values (in the order of the input rows) for rows whose
        score reaches the threshold.

    Raises:
        TypeError: If `rows` is not a list, if any element of `rows` is not a
                   dictionary, or if `threshold` is not a number (int or float).
    """
    # Validate rows
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    # Validate threshold
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be numeric (int or float)")

    result = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Element at index {idx} is not a dict: {type(row).__name__}")

        # Safely retrieve score; skip if missing or non-numeric
        score = row.get(score_field)
        if score is None:
            continue
        if not isinstance(score, (int, float)):
            continue

        # Check threshold
        if score >= threshold:
            name = row.get(name_field)
            result.append(name)

    return result
