from typing import List, Union

def filter_names_by_score_threshold(
    rows: List[dict],
    threshold: Union[int, float],
    name_field: str = "name",
    score_field: str = "score"
) -> List[str]:
    """
    Return names from a list of dictionaries where the score is at or above a threshold.

    Args:
        rows: A list of dictionaries, each containing at least `name_field` and `score_field` keys.
        threshold: Numeric threshold (score >= threshold is kept).
        name_field: Key to use for the name value (default "name").
        score_field: Key to use for the score value (default "score").

    Returns:
        List of names (strings) satisfying the threshold condition.

    Raises:
        TypeError: If `rows` is not a list, an element is not a dict, `threshold` is not numeric,
                   or a score value is not numeric.
        ValueError: If a dictionary is missing the required name or score keys.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be numeric (int or float)")

    result: List[str] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Element at index {idx} is not a dictionary")
        if name_field not in row or score_field not in row:
            raise ValueError(
                f"Dictionary at index {idx} missing required keys "
                f"'{name_field}' and/or '{score_field}'"
            )
        score = row[score_field]
        if not isinstance(score, (int, float)):
            raise TypeError(
                f"Score value at index {idx} (key '{score_field}') is not numeric"
            )
        if score >= threshold:
            result.append(row[name_field])

    return result
