def filter_names_by_score(
    rows: list[dict],
    threshold: float,
    name_field: str = "name",
    score_field: str = "score",
) -> list[str]:
    """
    Return a list of names from rows where the score meets or exceeds a threshold.

    Args:
        rows: A list of dictionaries representing records.
        threshold: Minimum score (inclusive) for a row to be selected.
        name_field: Key in each dictionary that holds the name. Defaults to "name".
        score_field: Key in each dictionary that holds the numeric score. Defaults to "score".

    Returns:
        A list of name strings corresponding to rows with score >= threshold.

    Raises:
        TypeError: If rows is not a list of dicts, or a score value is non-numeric.
        KeyError: If a row is missing one of the required keys.
        ValueError: If a required field value is None.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")

    filtered_names: list[str] = []

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"row at index {idx} must be a dictionary")

        # Check required keys are present
        if name_field not in row:
            raise KeyError(f"row at index {idx} missing key: {name_field!r}")
        if score_field not in row:
            raise KeyError(f"row at index {idx} missing key: {score_field!r}")

        name_val = row[name_field]
        score_val = row[score_field]

        # Validate non-null
        if name_val is None:
            raise ValueError(f"row at index {idx}: value for {name_field!r} is None")
        if score_val is None:
            raise ValueError(f"row at index {idx}: value for {score_field!r} is None")

        # Validate score is numeric
        if not isinstance(score_val, (int, float)):
            raise TypeError(
                f"row at index {idx}: {score_field!r} must be int or float, "
                f"got {type(score_val).__name__}"
            )

        if score_val >= threshold:
            filtered_names.append(name_val)

    return filtered_names
