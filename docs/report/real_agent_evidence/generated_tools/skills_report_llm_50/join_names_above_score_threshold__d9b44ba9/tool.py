import csv
import io
from typing import Union


def join_names_above_score_threshold(csv_text: str, threshold: Union[int, float]) -> str:
    """
    Parse a CSV string containing 'name' and 'score' columns, filter rows where
    score is strictly greater than the given threshold, and return the names
    joined by a comma and space, preserving row order.

    Args:
        csv_text: Non-empty string with CSV data, including a header row that
                  contains at least 'name' and 'score' columns.
        threshold: Numeric threshold; rows with a score greater than this value
                   will be included.

    Returns:
        A string of matching names separated by ", ". If no rows exceed the
        threshold, an empty string is returned.

    Raises:
        ValueError: If csv_text is empty or not a string, if the required columns
                    are missing, or if a score value cannot be converted to float.
        TypeError: If threshold is not a number.
    """
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string")

    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number (int or float)")

    csv_file = io.StringIO(csv_text)
    reader = csv.DictReader(csv_file)

    if reader.fieldnames is None:
        raise ValueError("CSV data has no header row")

    if 'name' not in reader.fieldnames or 'score' not in reader.fieldnames:
        raise ValueError("CSV must contain 'name' and 'score' columns")

    selected_names: list[str] = []

    for row in reader:
        try:
            score = float(row['score'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid score value in row {reader.line_num}: {row.get('score')!r}") from e

        if score > threshold:
            # 'name' column is guaranteed to exist, but may be empty
            selected_names.append(row['name'])

    return ", ".join(selected_names)
