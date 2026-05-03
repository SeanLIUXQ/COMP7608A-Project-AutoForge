from typing import Any

def filter_names_by_score_threshold(rows: list[dict[str, Any]], threshold: float) -> list[str]:
    """
    Return a list of names from rows whose 'score' is >= threshold.

    Args:
        rows: A list of dictionaries. Each dictionary should contain 'name'
              and 'score' keys; malformed entries are silently skipped.
        threshold: A numeric value to compare scores against.

    Returns:
        A list of name strings from rows that satisfy score >= threshold.

    Raises:
        TypeError: If rows is not a list or threshold is not numeric.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number")

    result: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if 'name' not in row or 'score' not in row:
            continue
        score = row['score']
        if not isinstance(score, (int, float)):
            continue
        if score >= threshold:
            result.append(row['name'])
    return result
