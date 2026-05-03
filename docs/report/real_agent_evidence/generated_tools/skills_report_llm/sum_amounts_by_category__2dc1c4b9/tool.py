def sum_amounts_by_category(
    records: list[dict], cat_field: str = "cat", amt_field: str = "amt"
) -> dict:
    """Sum numeric amounts grouped by category.

    Args:
        records: A list of dictionaries, each containing at least a category
            field and an amount field.
        cat_field: Name of the category key in each record (default "cat").
        amt_field: Name of the numeric amount key in each record (default "amt").

    Returns:
        A dictionary mapping each distinct category value to the sum of
        its corresponding amounts.

    Raises:
        TypeError: If `records` is not a list, any element is not a dict,
                   or an amount is not a number.
        ValueError: If a record is missing the required category or amount field.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")

    totals: dict = {}
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise TypeError(f"Record at index {idx} is not a dictionary")
        if cat_field not in rec:
            raise ValueError(f"Record at index {idx} missing category field '{cat_field}'")
        if amt_field not in rec:
            raise ValueError(f"Record at index {idx} missing amount field '{amt_field}'")

        cat = rec[cat_field]
        amt = rec[amt_field]
        if not isinstance(amt, (int, float)):
            raise TypeError(
                f"Amount for category '{cat}' must be a number, got {type(amt).__name__}"
            )

        totals[cat] = totals.get(cat, 0) + amt

    return totals
