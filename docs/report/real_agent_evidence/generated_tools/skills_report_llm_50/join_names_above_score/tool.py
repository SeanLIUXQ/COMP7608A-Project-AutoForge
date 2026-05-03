import csv
import io
from typing import Union


def join_names_above_score(
    csv_text: str,
    threshold: float,
    name_field: str = "name",
    score_field: str = "score",
) -> str:
    """
    Parse a CSV string, filter rows where the score is strictly greater than
    a threshold, and return a comma-separated string of the corresponding names.

    Args:
        csv_text: String containing CSV data with a header row.
        threshold: Numeric threshold (floats and ints accepted).
        name_field: Name of the column containing the names (default "name").
        score_field: Name of the column containing the numerical score (default "score").

    Returns:
        A comma-separated string of names whose scores exceed the threshold.

    Raises:
        ValueError: If csv_text is empty or not a string, if threshold is not numeric,
                    if the header does not contain the required fields, or if any
                    score value cannot be converted to a float.
    """
    # Validate inputs
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string.")
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a number.")

    # Parse CSV
    with io.StringIO(csv_text) as f:
        reader = csv.DictReader(f)
        if not (name_field in reader.fieldnames and score_field in reader.fieldnames):
            raise ValueError(
                f"CSV header must contain both '{name_field}' and '{score_field}'."
            )
        rows = list(reader)

    names = []
    for row in rows:
        # Strictly greater than threshold
        try:
            score_val = float(row[score_field])
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Non-numeric value in field '{score_field}': {row.get(score_field)}"
            ) from exc

        if score_val > threshold:
            names.append(row[name_field])

    return ", ".join(names)
