import csv
import io
from typing import Optional

def join_names_above_score_threshold(
    csv_text: str,
    threshold: float,
    name_field: str = "name",
    score_field: str = "score",
    delimiter: Optional[str] = None,
) -> str:
    """
    Extract names from a CSV string where the score exceeds a threshold.

    Parses the CSV, detects column names (default "name" and "score"),
    keeps rows with score > threshold, and returns the names joined by
    comma + space in original order.  Returns an empty string if no
    rows qualify.

    Args:
        csv_text: Non-empty string in CSV format with a header row.
        threshold: Numeric threshold; only rows with score > threshold are kept.
        name_field: Name of the column containing the name (default 'name').
        score_field: Name of the column containing the score (default 'score').
        delimiter: Optional explicit delimiter; if None, the delimiter is
                   detected automatically (falls back to comma).

    Returns:
        Comma-and-space-separated string of matching names.

    Raises:
        ValueError: If csv_text is empty, threshold is not numeric, required
                    columns are missing, or a score value cannot be converted.
    """
    # --- validation ---
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("csv_text must be a non-empty string.")
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be numeric (int or float).")

    # --- detect / determine dialect ---
    sample = csv_text[:2048]  # enough for sniffing
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        # fallback: comma
        dialect = csv.excel

    if delimiter is not None:
        # override delimiter if explicitly given
        dialect.delimiter = delimiter

    # --- parse ---
    reader = csv.reader(io.StringIO(csv_text), dialect)
    try:
        header = next(reader)
    except StopIteration:
        # No header row – treat as empty result
        return ""

    # Normalise header cells: strip whitespace
    header = [h.strip() for h in header]

    try:
        name_idx = header.index(name_field)
    except ValueError:
        raise ValueError(f"CSV must contain a '{name_field}' column. Found: {header}")

    try:
        score_idx = header.index(score_field)
    except ValueError:
        raise ValueError(f"CSV must contain a '{score_field}' column. Found: {header}")

    # --- filter and collect names ---
    qualified_names = []
    for row in reader:
        # row may have fewer fields; pad with empty strings for safety
        if len(row) <= max(name_idx, score_idx):
            continue  # or raise? We'll skip malformed rows gracefully.
        try:
            score_val = float(row[score_idx])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid score value in row: {row}")
        if score_val > threshold:
            qualified_names.append(row[name_idx].strip())

    return ", ".join(qualified_names)
