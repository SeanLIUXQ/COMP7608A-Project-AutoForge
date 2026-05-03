import csv
import io
from typing import Union

def join_names_above_threshold(
    csv_text: str,
    threshold: Union[int, float],
    name_field: str = "name",
    score_field: str = "score",
    delimiter: str = ",",
    quotechar: str = '"'
) -> str:
    """
    Parse CSV and return a comma-separated string of names where score > threshold.

    Args:
        csv_text: Non-empty CSV string with a header row.
        threshold: Numeric threshold; rows with score strictly greater are included.
        name_field: Header name for the name column (default 'name').
        score_field: Header name for the numeric score column (default 'score').
        delimiter: CSV field delimiter (default ',').
        quotechar: Character used for quoting fields (default '"').

    Returns:
        A string of matching names joined by ', '. If no rows match, returns ''.

    Raises:
        ValueError: If csv_text is empty/not a string, threshold is not numeric,
                    required fields are missing, or a score cannot be converted to float.
    """
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string")
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a number")

    reader = csv.DictReader(
        io.StringIO(csv_text),
        delimiter=delimiter,
        quotechar=quotechar,
    )

    if reader.fieldnames is None:
        return ""  # header only, no data

    missing = [f for f in (name_field, score_field) if f not in reader.fieldnames]
    if missing:
        raise ValueError(
            f"Missing required column(s) in CSV header: {', '.join(missing)}"
        )

    names = []
    for row in reader:
        raw = row.get(score_field, "")
        try:
            score = float(raw)
        except (ValueError, TypeError):
            raise ValueError(
                f"Could not convert score '{raw}' to float "
                f"(row number {reader.line_num})"
            ) from None
        if score > threshold:
            names.append(row[name_field])

    return ", ".join(names)
