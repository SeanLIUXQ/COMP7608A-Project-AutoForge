def sum_amounts_by_category(
    rows: list[dict],
    category_field: str = "category",
    amount_field: str = "amount",
) -> dict:
    """
    Sum numeric amounts grouped by a category field from a list of dictionaries.

    Args:
        rows: List of dictionaries, each containing at least the specified
              category and amount fields.
        category_field: Key for the category (default 'category').
        amount_field: Key for the numeric amount (default 'amount').

    Returns:
        A dictionary mapping each category to the total sum of its amounts
        as a float.

    Raises:
        TypeError: If rows is not a list.
        ValueError: If any row is not a dictionary, if a row is missing the
                    required fields, or if the amount cannot be converted to float.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")

    totals: dict[str, float] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {idx} is not a dictionary, got {type(row).__name__}")

        if category_field not in row or amount_field not in row:
            raise ValueError(
                f"Row {idx} missing required key(s): "
                f"'{category_field}' or '{amount_field}'"
            )

        category = row[category_field]
        try:
            amount = float(row[amount_field])
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Row {idx}: cannot convert amount to float: {exc}"
            ) from exc

        totals[category] = totals.get(category, 0.0) + amount

    return totals
