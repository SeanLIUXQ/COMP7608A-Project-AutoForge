import math
from typing import Any, List, Union

def filter_names_by_score_threshold(
    records: List[dict],
    threshold: Union[int, float],
    score_field: str = "score",
    name_field: str = "name"
) -> List[Any]:
    """Return names from a list of dictionaries where the score meets or exceeds a threshold.

    Args:
        records: A list of dictionaries, each expected to contain the given score and name fields.
        threshold: The minimum numeric score required for inclusion (inclusive).
        score_field: The key used to look up the score value. Defaults to "score".
        name_field: The key used to look up the name value. Defaults to "name".

    Returns:
        A list of name values from the dictionaries whose score satisfies the threshold.

    Raises:
        TypeError: If `records` is not a list, an item is not a dictionary, or the score value
            is not a number.
        ValueError: If `threshold` is not a finite number.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be an int or float")
    if isinstance(threshold, float) and (math.isnan(threshold) or math.isinf(threshold)):
        raise ValueError("threshold must be a finite number")

    result: List[Any] = []
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise TypeError(
                f"record at index {idx} must be a dict, got {type(rec).__name__}"
            )
        # Missing fields are silently skipped, as per the described logic.
        if score_field in rec and name_field in rec:
            score_val = rec[score_field]
            if not isinstance(score_val, (int, float)):
                raise TypeError(
                    f"score value in record {idx} must be numeric, got {type(score_val).__name__}"
                )
            if score_val >= threshold:
                result.append(rec[name_field])

    return result
