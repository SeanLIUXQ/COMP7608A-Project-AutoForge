import csv
import io
from typing import Union

def join_names_above_threshold(
    csv_text: str,
    threshold: float,
    name_field: str = "name",
    score_field: str = "score",
    separator: str = ", "
) -> str:
    """
    Parse a CSV string, filter rows where the score strictly exceeds a threshold,
    and return the names joined by a configurable separator.

    Args:
        csv_text: Non-empty CSV string with at least a header row.
        threshold: Numeric threshold; rows with score > threshold are kept.
        name_field: Column name containing the name value (default "name").
        score_field: Column name containing the numeric score (default "score").
        separator: String used to join the matching names (default ", ").

    Returns:
        A single string of joined names, or an empty string if no rows match.

    Raises:
        ValueError: If csv_text is empty, not a string, or missing required columns;
                    or if threshold cannot be interpreted as a float.
    """
    if not isinstance(csv_text, str):
        raise ValueError("csv_text must be a string")
    if not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string")

    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        raise ValueError("threshold must be convertible to float") from None

    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)

    if reader.fieldnames is None:
        raise ValueError("Unable to read CSV header; csv_text may be empty")
    if name_field not in reader.fieldnames:
        raise ValueError(f"Required name column '{name_field}' missing from CSV headers")
    if score_field not in reader.fieldnames:
        raise ValueError(f"Required score column '{score_field}' missing from CSV headers")

    names = []
    for row in reader:
        try:
            score = float(row[score_field])
        except (ValueError, TypeError):
            # Skip rows where the score is not a valid number
            continue
        if score > threshold:
            names.append(row[name_field])

    return separator.join(names)
