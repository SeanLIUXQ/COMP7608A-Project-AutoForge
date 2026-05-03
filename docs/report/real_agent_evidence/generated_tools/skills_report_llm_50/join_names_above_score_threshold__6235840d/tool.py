import csv
import io
from typing import Any

def join_names_above_score_threshold(
    csv_text: str,
    threshold: float,
    name_col: str = "name",
    score_col: str = "score",
    separator: str = ", "
) -> str:
    """
    Parse a CSV string, filter rows where a score column exceeds a threshold,
    extract the name column values, and join them into a single string.

    Args:
        csv_text: A non-empty string containing CSV data with a header row.
        threshold: Only rows with a score strictly greater than this value are kept.
        name_col: Header name for the column that provides the name strings.
                  Defaults to 'name'.
        score_col: Header name for the numeric score column. Defaults to 'score'.
        separator: String used to join the filtered names. Defaults to ', '.

    Returns:
        A single string of matched names joined by the separator.  Returns an
        empty string when no rows satisfy the condition.

    Raises:
        ValueError: If csv_text is empty, required columns are missing, or a
                    score cannot be converted to float.
        TypeError: If threshold is not a number.
    """
    # 1. Validate inputs
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number")

    # 2. Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    if reader.fieldnames is None:
        raise ValueError("CSV header row is missing")
    if name_col not in reader.fieldnames:
        raise ValueError(f"Column '{name_col}' not found in CSV header")
    if score_col not in reader.fieldnames:
        raise ValueError(f"Column '{score_col}' not found in CSV header")

    # 3. Filter and collect names
    names: list[str] = []
    for row_num, row in enumerate(reader, start=2):  # 1-indexed, +1 for header
        raw_score = row.get(score_col)
        try:
            score_val = float(raw_score) if raw_score is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Row {row_num}: cannot convert score '{raw_score}' to float"
            ) from exc
        if score_val is None:
            raise ValueError(f"Row {row_num}: missing score value in column '{score_col}'")

        if score_val > threshold:
            name_val = row.get(name_col, "")
            names.append(name_val if name_val is not None else "")

    return separator.join(names)
