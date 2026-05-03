def filter_and_extract_by_threshold(
    rows: list[dict],
    threshold: float,
    score_key: str = "score",
    name_key: str = "name"
) -> list[str]:
    """
    Filter a list of dictionaries by a numeric score threshold and extract names.

    Args:
        rows: A list of dictionaries, each containing at least `score_key` and
              `name_key` keys.
        threshold: Numeric threshold; rows with a score >= threshold are kept.
        score_key: Key for the score field (default 'score').
        name_key: Key for the name field (default 'name').

    Returns:
        A list of names from the rows that satisfy the threshold condition.

    Raises:
        TypeError: If `rows` is not a list, any element is not a dict,
                   or a score value is not a numeric type (int/float).
        ValueError: If any row is missing the required `score_key` or `name_key`.
    """
    # Input validation
    if not isinstance(rows, list):
        raise TypeError("First argument must be a list of dictionaries")

    result = []

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Element at index {idx} is not a dictionary")

        if score_key not in row:
            raise ValueError(f"Row at index {idx} missing required key '{score_key}'")
        if name_key not in row:
            raise ValueError(f"Row at index {idx} missing required key '{name_key}'")

        score_val = row[score_key]

        # Accept int and float, but reject bool because it subclasses int
        if not isinstance(score_val, (int, float)) or isinstance(score_val, bool):
            raise TypeError(
                f"Score value in row {idx} must be numeric (int or float), got {type(score_val).__name__}"
            )

        if score_val >= threshold:
            result.append(row[name_key])

    return result
