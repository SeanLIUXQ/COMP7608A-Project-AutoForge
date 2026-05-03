from typing import Any, List, Dict, Union

def get_names_by_score_threshold(rows: List[Dict[str, Any]], threshold: Union[int, float]) -> List[str]:
    """
    Given a list of dictionaries and a numeric threshold, return a list of 'name'
    values from dictionaries whose 'score' is greater than or equal to the threshold.

    Args:
        rows: List of dictionaries, each expected to contain keys 'score' (numeric)
              and 'name'.
        threshold: The minimum score value to include a name.

    Returns:
        A list of names (strings) satisfying the score >= threshold condition.

    Raises:
        ValueError: If input is not a list of dictionaries, or if any dictionary
                    is missing 'score' or 'name', or if 'score' is non-numeric.
    """
    if not isinstance(rows, list):
        raise ValueError("rows must be a list of dictionaries")

    names: List[str] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Item at index {idx} is not a dictionary")
        if "score" not in row:
            raise ValueError(f"Dictionary at index {idx} is missing key 'score'")
        if "name" not in row:
            raise ValueError(f"Dictionary at index {idx} is missing key 'name'")
        if not isinstance(row["score"], (int, float)):
            raise ValueError(f"Score at index {idx} is not numeric, got {type(row['score']).__name__}")

        if row["score"] >= threshold:
            names.append(row["name"])

    return names
