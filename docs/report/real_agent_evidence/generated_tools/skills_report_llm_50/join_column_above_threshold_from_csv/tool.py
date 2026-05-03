import csv
import io
from typing import Union


def join_column_above_threshold_from_csv(
    csv_text: str,
    threshold: Union[int, float],
    name_column: str = "name",
    score_column: str = "score",
) -> str:
    """
    Parse a CSV string, filter rows where a numeric column exceeds a threshold,
    and return a comma-separated string of values from another column.

    Args:
        csv_text: CSV-formatted string with a header row.
        threshold: Numeric threshold; rows with a score strictly greater than
                   this value are kept.
        name_column: Name of the column whose values are joined (default "name").
        score_column: Name of the numeric column used for filtering (default "score").

    Returns:
        A comma-separated string of the name_column values from rows that pass
        the threshold filter.

    Raises:
        TypeError: If inputs have incorrect types.
        ValueError: If column names are empty or not found in the CSV header,
                    or if score values cannot be converted to float.
    """
    # --- input validation ---
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number (int or float)")
    if not isinstance(name_column, str) or not name_column.strip():
        raise ValueError("name_column must be a non-empty string")
    if not isinstance(score_column, str) or not score_column.strip():
        raise ValueError("score_column must be a non-empty string")

    name_column = name_column.strip()
    score_column = score_column.strip()

    # --- parse CSV ---
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV text contains no header row")
    if name_column not in reader.fieldnames:
        raise ValueError(
            f"name_column '{name_column}' not found in CSV header: {reader.fieldnames}"
        )
    if score_column not in reader.fieldnames:
        raise ValueError(
            f"score_column '{score_column}' not found in CSV header: {reader.fieldnames}"
        )

    # --- filter and collect names ---
    names: list[str] = []
    for row in reader:
        score_str = row.get(score_column, "")
        try:
            score_value = float(score_str)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Could not convert score value '{score_str}' to float"
            ) from exc
        if score_value > threshold:
            names.append(row[name_column])

    return ",".join(names)
