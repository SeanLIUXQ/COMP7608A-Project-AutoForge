import csv
import io
from typing import List, Union


def filter_names_by_score_threshold(csv_text: str, threshold: Union[float, int]) -> List[str]:
    """
    Parse CSV text and return names where the score exceeds a given threshold.

    The CSV must have a header row containing at least the columns 'name' and 'score'.
    Rows with a non-numeric or missing 'score' value are silently skipped.

    Args:
        csv_text: Non-empty string containing CSV data with headers.
        threshold: Numeric value to compare scores against (int or float).

    Returns:
        List of 'name' values from rows where the score (as float) > threshold.

    Raises:
        ValueError: If csv_text is not a non-empty string, threshold is not a number,
                    or the CSV does not contain both 'name' and 'score' columns.
    """
    # Validate csv_text
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string")

    # Validate threshold
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a number (int or float)")

    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_text))

    # Ensure required columns exist
    if reader.fieldnames is None or 'name' not in reader.fieldnames or 'score' not in reader.fieldnames:
        raise ValueError("CSV must contain 'name' and 'score' header columns")

    names: List[str] = []
    for row in reader:
        score_raw = row.get('score', '')
        if not score_raw:
            continue
        try:
            score_val = float(score_raw)
        except (ValueError, TypeError):
            continue
        if score_val > threshold:
            name = row.get('name', '').strip()
            if name:  # keep non-empty names only
                names.append(name)

    return names
