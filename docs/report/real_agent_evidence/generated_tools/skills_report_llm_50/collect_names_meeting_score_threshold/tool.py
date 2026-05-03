from typing import Any, Dict, List, Union

def collect_names_meeting_score_threshold(
    rows: List[Dict[str, Any]],
    threshold: Union[int, float],
    score_field: str = "score",
    name_field: str = "name"
) -> List[Any]:
    """
    Collect the values of `name_field` from rows where `score_field` is at least `threshold`.

    Args:
        rows: A list of dictionaries to filter.
        threshold: The minimum numeric score value required (inclusive).
        score_field: The key in each dictionary that holds the numeric score.
            Defaults to "score".
        name_field: The key in each dictionary whose value is collected.
            Defaults to "name".

    Returns:
        A list of values from the `name_field` of rows that meet the score threshold.
        The type of each element depends on the underlying data.

    Raises:
        TypeError: If `rows` is not a list, `threshold` is not a number,
            or any row is not a dictionary.
        ValueError: If a row is missing the required `score_field` or `name_field`,
            or if the value for `score_field` is not a numeric type (int or float).
    """
    # 1. Validate overall types
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    # exclude booleans which are subclasses of int
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a numeric value (int or float)")

    collected: List[Any] = []

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"row at index {i} must be a dictionary, got {type(row).__name__}")

        # 2. Ensure required fields exist
        if score_field not in row:
            raise ValueError(f"row at index {i} is missing the score field '{score_field}'")
        if name_field not in row:
            raise ValueError(f"row at index {i} is missing the name field '{name_field}'")

        score_val = row[score_field]

        # 3. Ensure score field is numeric (not bool)
        if isinstance(score_val, bool) or not isinstance(score_val, (int, float)):
            raise ValueError(
                f"row at index {i}: score field '{score_field}' must be numeric (int or float), "
                f"got {type(score_val).__name__} with value {score_val!r}"
            )

        # 4. Check threshold condition
        if score_val >= threshold:
            collected.append(row[name_field])

    return collected
