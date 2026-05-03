def sum_by_category(rows: list[dict], category_field: str = "cat", value_field: str = "amt") -> dict:
    """
    Sum numeric values grouped by category from a list of dictionaries.

    Args:
        rows: A list of dictionaries, each containing at least the category
              and value fields.
        category_field: The dictionary key used for the category. Defaults to "cat".
        value_field: The dictionary key used for the numeric value. Defaults to "amt".

    Returns:
        A dictionary mapping each category (as found) to its total sum (as float).

    Raises:
        TypeError: If rows is not a list or if the field names are not strings.
    """
    # Validate input types
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries")
    if not isinstance(category_field, str):
        raise TypeError("category_field must be a string")
    if not isinstance(value_field, str):
        raise TypeError("value_field must be a string")

    totals: dict = {}

    for row in rows:
        if not isinstance(row, dict):
            # Skip non-dictionary entries; could alternatively raise a TypeError.
            continue

        cat = row.get(category_field)
        # Skip rows where the category field is missing or None
        if cat is None:
            continue

        raw_value = row.get(value_field, 0.0)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            # Gracefully treat non-convertible values as zero
            value = 0.0

        totals[cat] = totals.get(cat, 0.0) + value

    return totals
