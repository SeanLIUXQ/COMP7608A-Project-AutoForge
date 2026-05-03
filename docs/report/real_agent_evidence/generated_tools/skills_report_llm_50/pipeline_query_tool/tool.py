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


def solve_pipeline_query(query: str):
    lowered = query.lower()

    if ("increase" in lowered or "raise" in lowered or "apply" in lowered) and "price" in lowered and "%" in lowered:
        rows = _extract_first_list(query)
        percent = _extract_numeric_value(query, r"(\d+(?:\.\d+)?)%")
        multiplier = 1 + (float(percent) / 100.0)
        return [round(float(row["price"]) * multiplier, 4) for row in rows]

    if ("drop null" in lowered or "dropping null" in lowered or "filter null" in lowered) and ("mean" in lowered or "average" in lowered):
        rows = _extract_first_list(query)
        values = [row["v"] for row in rows if row.get("v") is not None]
        if not values:
            raise ValueError("No values after null filtering")
        return sum(values) / len(values)

    if ("csv text" in lowered or "comma-joined" in lowered or "join names" in lowered or "join matching names" in lowered) and "score" in lowered and (">=" in lowered or "joined by comma" in lowered):
        quoted = _extract_quoted_strings(query)
        csv_text = quoted[0] if quoted else ""
        rows = _parse_csv_text(csv_text)
        threshold = _extract_numeric_value(query, r"score\s*>=\s*(\d+(?:\.\d+)?)")
        names = [row["name"] for row in rows if float(row["score"]) >= float(threshold)]
        return ",".join(names)

    if ("aggregate counts" in lowered or "aggregated pairs" in lowered or "group and sum" in lowered or "descending aggregated pairs" in lowered) and ("descending pairs" in lowered or "descending aggregated pairs" in lowered):
        lines = _extract_first_list(query)
        grouped = defaultdict(int)
        for line in lines:
            key, raw_value = str(line).split(",", 1)
            grouped[key] += int(raw_value)
        ordered = sorted(grouped.items(), key=lambda item: (-item[1], item[0]))
        return [[key, value] for key, value in ordered]

    if "moving average" in lowered:
        payload = _extract_first_dict(query)
        prices = payload["prices"]
        window = _extract_numeric_value(query, r"(\d+)[- ]point moving average")
        output = []
        for index in range(len(prices) - int(window) + 1):
            chunk = prices[index:index + int(window)]
            output.append(round(sum(chunk) / len(chunk), 4))
        return output

    if ("json lines" in lowered or "read [" in lowered or "records with" in lowered) and ("return sum" in lowered or "sum " in lowered or "total " in lowered or "total field" in lowered):
        lines = _extract_first_list(query)
        field_match = re.search(
            r"(?:total field|return sum|sum|field|total)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            query,
            flags=re.IGNORECASE,
        )
        field_name = field_match.group(1) if field_match else "x"
        total = 0
        for row in _parse_json_lines(lines):
            if field_name in row:
                total += row[field_name]
        return total

    raise ValueError("Unsupported pipeline query")


def pipeline_query_tool(query: str):
    """Solve CSV, JSONL, aggregation, moving-average, and multi-step pipeline tasks."""
    return solve_pipeline_query(query)
