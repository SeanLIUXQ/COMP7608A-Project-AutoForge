import csv
import io
from typing import Any, Dict, List, Union

def join_names_above_threshold(
    csv_text: str,
    threshold: Union[int, float],
    name_column: str = "name",
    score_column: str = "score",
    separator: str = ", ",
) -> str:
    """
    Parse a CSV string and return a string containing the names (from `name_column`)
    of all rows whose score (in `score_column`) is strictly greater than `threshold`,
    joined by `separator`.

    Args:
        csv_text: A non-empty CSV string, including a header row.
        threshold: A numeric threshold for filtering.
        name_column: The header name of the column containing names.
        score_column: The header name of the column containing numeric scores.
        separator: The string used to join the selected names (default ", ").

    Returns:
        A string of joined names, or an empty string if no rows match.
    
    Raises:
        ValueError: If input types are invalid, CSV is malformed, required columns
                    are missing, or score values cannot be converted to float.
    """
    # --- Input validation ---
    if not isinstance(csv_text, str) or csv_text.strip() == "":
        raise ValueError("csv_text must be a non-empty string")
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be an int or float")
    if not isinstance(name_column, str) or not isinstance(score_column, str):
        raise ValueError("name_column and score_column must be strings")
    
    threshold = float(threshold)  # ensure float for comparison

    # --- Parse CSV ---
    f = io.StringIO(csv_text)
    try:
        reader = csv.DictReader(f)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}") from e

    if reader.fieldnames is None:
        raise ValueError("CSV header is empty or missing")
    
    fieldnames = reader.fieldnames
    for col in (name_column, score_column):
        if col not in fieldnames:
            raise ValueError(
                f"Required column '{col}' not found in header: {fieldnames}"
            )

    # --- Filter rows ---
    matching_names: List[str] = []
    for row_num, row in enumerate(reader, start=2):  # header is line 1
        try:
            score = float(row[score_column])
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid score value in row {row_num}, column '{score_column}': "
                f"{row[score_column]!r}"
            ) from e
        
        if score > threshold:
            matching_names.append(row[name_column])

    return separator.join(matching_names)
