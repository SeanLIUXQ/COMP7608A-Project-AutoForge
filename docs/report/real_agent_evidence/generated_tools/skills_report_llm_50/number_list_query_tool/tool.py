import ast
import csv
import io
import re
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import parse_qs, urlparse


def _extract_quoted_strings(query: str) -> list[str]:
    matches = re.findall(r"'([^']*)'|\"([^\"]*)\"", query)
    return [left or right for left, right in matches]


def _extract_balanced(query: str, opener: str, closer: str) -> str | None:
    start = query.find(opener)
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(query)):
        char = query[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return query[start:index + 1]
    return None


def _to_python_literal(text: str):
    normalized = re.sub(r"\bnull\b", "None", text, flags=re.IGNORECASE)
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    return ast.literal_eval(normalized)


def _extract_first_list(query: str):
    fragment = _extract_balanced(query, "[", "]")
    if fragment is None:
        raise ValueError("Missing list literal")
    return _to_python_literal(fragment)


def _extract_first_dict(query: str):
    fragment = _extract_balanced(query, "{", "}")
    if fragment is None:
        raise ValueError("Missing dict literal")
    return _to_python_literal(fragment)


def _extract_decimal_places(query: str, default: int = 2) -> int:
    lowered = query.lower()
    match = re.search(r"(\d+)\s*(?:decimal|decimals|dp)", lowered)
    if match:
        return int(match.group(1))
    if "one decimal" in lowered:
        return 1
    if "two decimals" in lowered:
        return 2
    if "three decimals" in lowered:
        return 3
    return default


def _extract_numeric_value(query: str, pattern: str):
    match = re.search(pattern, query, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Pattern not found: {pattern}")
    raw = match.group(1)
    return float(raw) if "." in raw else int(raw)


def _extract_tail_words(query: str, marker: str) -> str:
    lowered = query.lower()
    index = lowered.find(marker.lower())
    if index == -1:
        raise ValueError(f"Missing marker: {marker}")
    return query[index + len(marker):].strip(" ?.:\"'")


def _parse_csv_text(csv_text: str):
    reader = csv.DictReader(io.StringIO(csv_text))
    return list(reader)


def _parse_json_lines(lines):
    records = []
    for line in lines:
        records.append(_to_python_literal(line))
    return records


def _sum_by_category(rows):
    grouped = defaultdict(int)
    for row in rows:
        category = row.get("cat") or row.get("category")
        amount = row.get("amt", row.get("amount", 0))
        grouped[category] += amount
    return dict(grouped)


def _filter_names_by_score(rows, threshold):
    return [row["name"] for row in rows if float(row.get("score", 0)) >= float(threshold)]


def solve_number_query(query: str):
    lowered = query.lower()

    if "moving average" in lowered:
        raise ValueError("Use pipeline solver for moving average")

    if ("sort" in lowered or "order" in lowered) and ("ascending" in lowered or "small to large" in lowered):
        values = _extract_first_list(query)
        return sorted(values)

    if "average" in lowered or "mean" in lowered:
        values = _extract_first_list(query)
        if not values:
            raise ValueError("Cannot average empty list")
        for value in values:
            if not isinstance(value, (int, float)):
                raise ValueError("Average expects numeric list")
        return sum(values) / len(values)

    if "duplicate" in lowered or "first occurrences" in lowered:
        values = _extract_first_list(query)
        seen = set()
        ordered = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered

    if ("sum" in lowered or "add" in lowered) and ("rounded" in lowered or "decimal" in lowered or "dp" in lowered):
        values = _extract_first_list(query)
        decimals = _extract_decimal_places(query, default=1)
        return round(sum(values), decimals)

    if "bytes" in lowered and ("megabytes" in lowered or " mb" in lowered):
        bytes_value = _extract_numeric_value(query, r"(\d+)\s+bytes")
        decimals = _extract_decimal_places(query, default=2)
        return round(bytes_value / (1024 * 1024), decimals)

    raise ValueError("Unsupported number query")


def number_list_query_tool(query: str):
    """Solve sorting, averaging, deduplication, rounded sums, and byte-conversion tasks."""
    return solve_number_query(query)
