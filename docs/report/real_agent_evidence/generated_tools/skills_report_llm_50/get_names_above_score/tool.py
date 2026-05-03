from typing import Any, Union

def get_names_above_score(
    rows: list[dict[str, Any]],
    threshold: Union[int, float],
    score_field: str = "score",
    name_field: str = "name"
) -> list[Any]:
    """
    Filter rows by a score threshold and return the associated names.

    Args:
        rows: A list of dictionaries, each expected to contain at least the
            fields specified by `score_field` and `name_field`.
        threshold: Only rows where the score value is >= threshold are included.
        score_field: Key to look up the numeric score value (default 'score').
        name_field: Key to look up the name value (default 'name').

    Returns:
        A list of the name values from rows meeting the threshold criterion.

    Raises:
        TypeError: If `rows` is not a list of dictionaries.
        ValueError: If any row is missing the required fields, or if a score
            value is not numeric.
    """
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise TypeError("rows must be a list of dictionaries")

    result: list[Any] = []
    for row in rows:
        if score_field not in row or name_field not in row:
            raise ValueError(
                f"Each row must contain '{score_field}' and '{name_field}'"
            )
        score = row[score_field]
        if not isinstance(score, (int, float)):
            raise ValueError(
                f"Score value must be numeric, got {type(score).__name__}"
            )
        if score >= threshold:
            result.append(row[name_field])
    return result
