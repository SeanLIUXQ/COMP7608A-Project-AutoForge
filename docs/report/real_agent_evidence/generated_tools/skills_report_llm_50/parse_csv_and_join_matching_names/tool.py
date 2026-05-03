import csv
import io
from typing import Union

def parse_csv_and_join_matching_names(
    csv_text: str,
    name_col: str,
    score_col: str,
    threshold: Union[int, float],
    separator: str = ", "
) -> str:
    """Parse a CSV string and return names from rows whose score exceeds a threshold.

    Args:
        csv_text: CSV data as a string.
        name_col: The header name of the column containing names.
        score_col: The header name of the column containing numeric scores.
        threshold: The score threshold (exclusive). Rows with score > threshold are included.
        separator: String used to join the matching names.

    Returns:
        A single string of names separated by `separator`. If no rows match or the input is
        effectively empty, returns an empty string.

    Raises:
        TypeError: If input types are incorrect.
        ValueError: If a score value cannot be converted to float, or if threshold is not numeric.
    """
    # Validate types
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    if not isinstance(name_col, str):
        raise TypeError("name_col must be a string")
    if not isinstance(score_col, str):
        raise TypeError("score_col must be a string")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")

    # Empty input -> empty result
    if not csv_text.strip():
        return ""

    # Parse CSV
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)

    matching_names = []
    for row in reader:
        # Skip rows that do not contain both required columns
        if name_col not in row or score_col not in row:
            continue
        
        raw_score = row[score_col].strip()
        try:
            score = float(raw_score)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Could not convert score '{row[score_col]}' to float"
            ) from exc

        if score > threshold:
            matching_names.append(row[name_col].strip())

    return separator.join(matching_names)
