import csv
from typing import Any

def filter_csv_names_by_score(
    csv_text: str,
    threshold: float,
    name_column: str = "name",
    score_column: str = "score",
    delimiter: str = ", "
) -> str:
    """
    Return a delimited string of names from rows where the score exceeds the threshold.

    Parameters
    ----------
    csv_text : str
        CSV text with a header row.
    threshold : float
        Numerical threshold; rows with score > threshold are selected.
    name_column : str, optional
        Name of the column holding the names (default "name").
    score_column : str, optional
        Name of the column holding the numeric score (default "score").
    delimiter : str, optional
        String used to join the matched names (default ", ").

    Returns
    -------
    str
        Joined names delimited by `delimiter`. If no rows match, returns an empty string.

    Raises
    ------
    TypeError
        If `csv_text` is not a string or `threshold` is not a number.
    ValueError
        If the required column names are not found in the header, or if a score
        value cannot be converted to float.
    """
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number")

    lines = csv_text.splitlines()
    if not lines:
        return ""

    reader = csv.reader(lines)
    try:
        header = next(reader)
    except StopIteration:
        return ""

    # Find column indices
    try:
        name_idx = header.index(name_column)
    except ValueError:
        raise ValueError(f"name_column '{name_column}' not found in header") from None
    try:
        score_idx = header.index(score_column)
    except ValueError:
        raise ValueError(f"score_column '{score_column}' not found in header") from None

    names: list[str] = []
    for row in reader:
        # Skip empty rows
        if not row:
            continue
        try:
            score_str = row[score_idx]
        except IndexError:
            # Row has fewer columns than expected; skip or raise?
            # For robustness, skip malformed rows.
            continue
        try:
            score_val = float(score_str)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid score value '{score_str}' in row {reader.line_num}"
            ) from e
        if score_val > threshold:
            try:
                names.append(row[name_idx])
            except IndexError:
                # Row missing the name column; skip it.
                continue

    return delimiter.join(names)
