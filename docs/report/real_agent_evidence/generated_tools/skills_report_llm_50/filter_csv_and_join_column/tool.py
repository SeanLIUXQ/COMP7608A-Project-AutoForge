import csv
import io
from typing import Union

def filter_csv_and_join_column(
    csv_text: str,
    threshold: Union[int, float],
    name_col: str,
    score_col: str,
    separator: str = ", "
) -> str:
    """
    Parse a CSV (with a header row), keep rows where the numeric value of
    `score_col` can be converted to float and is strictly greater than
    `threshold`, then join the values of `name_col` using `separator`.

    Args:
        csv_text: CSV data as a string (first row is header).
        threshold: Numeric threshold (exclusive).
        name_col: Column name whose values are collected.
        score_col: Column name whose numeric values are compared.
        separator: String used to join the collected names. Default ', '.

    Returns:
        A string containing the joined names from rows meeting the condition.

    Raises:
        TypeError: If input types are invalid.
        ValueError: If required columns are missing (implicitly via csv.DictReader).
    """
    # Validate types
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise TypeError("threshold must be a number (int or float)")
    if not isinstance(name_col, str):
        raise TypeError("name_col must be a string")
    if not isinstance(score_col, str):
        raise TypeError("score_col must be a string")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")

    # Parse CSV
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)

    # Collect matching names
    names = []
    for row in reader:
        # If either column is missing from the row, DictReader returns None;
        # we skip such rows to avoid errors during conversion or missing data.
        score_str = row.get(score_col)
        if score_str is None:
            continue
        try:
            score_val = float(score_str)
        except (ValueError, TypeError):
            # Skip rows where the value cannot be converted
            continue

        if score_val > threshold:
            name_val = row.get(name_col)
            # If name column is missing, we still include an empty string
            # to keep alignment clear (consistent with typical expectations).
            names.append(name_val if name_val is not None else "")

    return separator.join(names)
