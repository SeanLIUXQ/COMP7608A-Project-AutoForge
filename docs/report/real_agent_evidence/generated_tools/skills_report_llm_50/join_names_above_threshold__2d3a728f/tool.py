import csv
import io

def join_names_above_threshold(
    csv_text: str,
    threshold: float,
    name_column: str,
    score_column: str,
    separator: str = ', '
) -> str:
    """Filter CSV rows by a numeric score threshold and return the joined name values.

    Parses the given CSV text (comma delimiter, header row expected) and extracts
    the values from `name_column` for every row where the value of `score_column`
    is strictly greater than `threshold`.  Rows that lack either column, or have a
    non-numeric score, are silently skipped.

    Args:
        csv_text:    CSV formatted string with a header row and comma delimiters.
        threshold:   Numeric threshold; only rows with a score > threshold are kept.
        name_column: Name of the column containing the names to extract.
        score_column: Name of the column containing numeric scores.
        separator:   String used to join the selected names. Defaults to ', '.

    Returns:
        A single string consisting of the qualifying names joined by `separator`.
        If no names qualify, the empty string is returned.

    Raises:
        TypeError: If any argument has an incorrect type.
    """
    # ---- input validation ----
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    if not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a number (int or float)")
    if not isinstance(name_column, str):
        raise TypeError("name_column must be a string")
    if not isinstance(score_column, str):
        raise TypeError("score_column must be a string")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")

    # ---- parse CSV ----
    with io.StringIO(csv_text) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:          # empty input, no header
            return ""

        names = []
        for row in reader:
            # ensure both required columns are present (DictReader may fill missing
            # fields with None, but the key will exist only if it is in the header)
            if name_column not in row or score_column not in row:
                continue

            name = row[name_column]
            if name is None:                   # missing name value
                continue

            score_str = row[score_column]
            if score_str is None:              # missing score value
                continue

            try:
                score_val = float(score_str)
            except (ValueError, TypeError):
                # non-numeric score
                continue

            if score_val > threshold:
                names.append(name)

    return separator.join(names)
