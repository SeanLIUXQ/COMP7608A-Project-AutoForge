from typing import List, Dict, Union

def filter_names_by_score_threshold(
    rows: List[Dict],
    threshold: Union[float, int],
    score_key: str = "score",
    name_key: str = "name"
) -> List[str]:
    """
    Return a list of names taken from rows whose numeric score meets or exceeds the given threshold.

    Args:
        rows: A list of dictionaries; elements that are not dicts are silently ignored.
        threshold: The minimum score (inclusive) required for inclusion.
        score_key: The key in each dict holding the score (default "score").
        name_key: The key holding the name to extract (default "name").

    Returns:
        A list of strings (the names) from qualifying rows.

    Raises:
        TypeError: If *rows* is not a list or *threshold* is not a number.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number")

    results: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if score_key in row:
            try:
                score = float(row[score_key])
            except (TypeError, ValueError):
                # Score is not convertible to a number – skip this row
                continue
            if score >= threshold:
                # If name_key is missing, a KeyError is raised (callers should ensure it exists)
                results.append(row[name_key])
    return results
