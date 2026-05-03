import csv
import io
from typing import Union

def parse_csv_and_join_names(
    csv_text: str,
    threshold: float,
    name_col: str = "name",
    score_col: str = "score",
    delimiter: str = ", "
) -> str:
    """
    Parse CSV text, filter rows where a score column is greater than a threshold,
    and return the names from matching rows joined by a configurable delimiter.

    Args:
        csv_text: CSV contents with a header row.
        threshold: Numeric threshold; rows with score > threshold are kept.
        name_col: Name of the column containing the names (default "name").
        score_col: Name of the column containing the scores (default "score").
        delimiter: Separator used when joining the filtered names (default ", ").

    Returns:
        A string of joined names from rows that satisfy score > threshold.
        Returns an empty string if no rows pass the filter.

    Raises:
        TypeError: If csv_text is not a string or threshold is not numeric.
        ValueError: If csv_text is empty, required columns are missing,
                    or a score value cannot be converted to float.
    """
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string.")
    if not csv_text.strip():
        raise ValueError("csv_text must not be empty or only whitespace.")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number (int or float).")

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row.")
    if name_col not in reader.fieldnames:
        raise ValueError(f"Column '{name_col}' not found in CSV header.")
    if score_col not in reader.fieldnames:
        raise ValueError(f"Column '{score_col}' not found in CSV header.")

    names: list[str] = []
    for row in reader:
        raw_score = row[score_col]
        try:
            score = float(raw_score)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Row {reader.line_num}: score value '{raw_score}' cannot be converted to float."
            ) from exc
        if score > threshold:
            names.append(row[name_col])

    return delimiter.join(names)
