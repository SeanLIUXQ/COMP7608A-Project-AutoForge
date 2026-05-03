def sum_amounts_by_category(
    rows: list[dict],
    category_field: str = "category",
    amount_field: str = "amount"
) -> dict[str, float]:
    """Sum amounts by category across a list of row dictionaries.

    Args:
        rows: List of dictionaries, each containing at least category_field
            and amount_field keys.
        category_field: Name of the key holding the category value
            (default 'category').
        amount_field: Name of the key holding the numeric amount
            (default 'amount').

    Returns:
        Dictionary mapping each category to the total sum of amounts.

    Raises:
        TypeError: If rows is not a list, or any element is not a dict.
        KeyError: If a row dictionary is missing the category_field or
            amount_field key.
        ValueError: If an amount cannot be converted to a float.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries.")

    totals: dict[str, float] = {}

    for row_idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Element at index {row_idx} is not a dict.")

        if category_field not in row:
            raise KeyError(
                f"Row {row_idx} is missing the category field "
                f"'{category_field}'."
            )
        if amount_field not in row:
            raise KeyError(
                f"Row {row_idx} is missing the amount field "
                f"'{amount_field}'."
            )

        try:
            amount = float(row[amount_field])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Amount at row {row_idx} cannot be converted to float: "
                f"{row[amount_field]!r}"
            ) from exc

        cat = row[category_field]
        totals[cat] = totals.get(cat, 0.0) + amount

    return totals
