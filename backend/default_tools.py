from __future__ import annotations

import json
import shutil
from pathlib import Path
from textwrap import dedent
from typing import Any

from agents.packager import create_skill_bundle
from shared.constants import BACKEND_SKILLS_DIR
from shared.schemas import ToolParameter, ToolSchema


_COMMON_QUERY_HELPERS = dedent(
    '''
    import ast
    import csv
    import io
    import re
    from collections import Counter, defaultdict
    from datetime import datetime
    from urllib.parse import parse_qs, urlparse


    def _extract_quoted_strings(query: str) -> list[str]:
        matches = re.findall(r"'([^']*)'|\\"([^\\"]*)\\"", query)
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
        normalized = re.sub(r"\\bnull\\b", "None", text, flags=re.IGNORECASE)
        normalized = re.sub(r"\\btrue\\b", "True", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\\bfalse\\b", "False", normalized, flags=re.IGNORECASE)
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
        match = re.search(r"(\\d+)\\s*(?:decimal|decimals|dp)", lowered)
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
        return query[index + len(marker):].strip(" ?.:\\"'")


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
    '''
).strip()


_TEXT_SOLVER = dedent(
    '''
    def solve_text_query(query: str):
        lowered = query.lower()
        quoted = _extract_quoted_strings(query)

        if "vowel" in lowered:
            if quoted:
                target = quoted[0]
            else:
                target = query.strip().split()[-1].strip("?.")
            return sum(1 for char in target.lower() if char in "aeiou")

        if "reverse" in lowered or "backwards" in lowered:
            if quoted:
                target = quoted[0]
            elif " of " in lowered:
                target = _extract_tail_words(query, " of ")
            elif " string " in lowered:
                target = _extract_tail_words(query, " string ")
            else:
                target = query.strip().split()[-1].strip("?.")
            return target[::-1]

        if "title case" in lowered or "title-case" in lowered:
            target = quoted[-1] if quoted else _extract_tail_words(query, " to ")
            return " ".join(part.capitalize() for part in target.split())

        if "phone" in lowered and ("digits" in lowered or "digits only" in lowered or "digit-only" in lowered):
            target = quoted[0] if quoted else query
            return "".join(char for char in target if char.isdigit())

        if "top" in lowered and "token" in lowered:
            token_text = quoted[0] if quoted else _extract_tail_words(query, " in ")
            top_n = _extract_numeric_value(query, r"top\\s+(\\d+)") if "top " in lowered else 2
            counts = Counter(token_text.split())
            ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            return [item[0] for item in ordered[:top_n]]

        raise ValueError("Unsupported text query")
    '''
).strip()


_NUMBER_SOLVER = dedent(
    '''
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
            bytes_value = _extract_numeric_value(query, r"(\\d+)\\s+bytes")
            decimals = _extract_decimal_places(query, default=2)
            return round(bytes_value / (1024 * 1024), decimals)

        raise ValueError("Unsupported number query")
    '''
).strip()


_STRUCTURED_SOLVER = dedent(
    '''
    def solve_structured_query(query: str):
        lowered = query.lower()

        if "keys" in lowered and ("sorted" in lowered or "alphabetically" in lowered or "sort" in lowered):
            obj = _extract_first_dict(query)
            return sorted(obj.keys())

        if "sum field" in lowered or "total for field" in lowered or "add up field" in lowered or "total field" in lowered:
            rows = _extract_first_list(query)
            if any(not isinstance(row, dict) for row in rows):
                raise ValueError("Field summation expects row dictionaries")
            field_match = re.search(
                r"(?:sum field|field|total field)\\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                query,
                flags=re.IGNORECASE,
            )
            field_name = field_match.group(1) if field_match else "x"
            return sum(row[field_name] for row in rows if field_name in row)

        if (("return names" in lowered or "list names" in lowered or "output names" in lowered or "names only" in lowered or "keep names" in lowered) and ">=" in lowered):
            rows = _extract_first_list(query)
            threshold = _extract_numeric_value(query, r">=\\s*(\\d+(?:\\.\\d+)?)")
            return _filter_names_by_score(rows, threshold)

        if "first letter" in lowered or "first-letter" in lowered:
            words = _extract_first_list(query)
            grouped = defaultdict(list)
            for word in words:
                grouped[str(word)[0].lower()].append(word)
            return dict(sorted(grouped.items()))

        if "contains key" in lowered or "contain key" in lowered or "exists in json" in lowered or ("check key" in lowered and "inside" in lowered):
            quoted = _extract_quoted_strings(query)
            if len(quoted) < 2:
                raise ValueError("Expected JSON text and key")
            json_text = quoted[0]
            key = quoted[-1]
            for item in quoted:
                if item.strip().startswith("{"):
                    json_text = item
                    break
            for item in quoted:
                if not item.strip().startswith("{"):
                    key = item
                    break
            obj = _to_python_literal(json_text)
            return key in obj

        if (
            "aggregate total by category" in lowered
            or "aggregate totals by category" in lowered
            or "category totals" in lowered
            or "total amount by category" in lowered
            or "amounts by category" in lowered
        ):
            rows = _extract_first_list(query)
            return _sum_by_category(rows)

        raise ValueError("Unsupported structured query")
    '''
).strip()


_PIPELINE_SOLVER = dedent(
    '''
    def solve_pipeline_query(query: str):
        lowered = query.lower()

        if ("increase" in lowered or "raise" in lowered or "apply" in lowered) and "price" in lowered and "%" in lowered:
            rows = _extract_first_list(query)
            percent = _extract_numeric_value(query, r"(\\d+(?:\\.\\d+)?)%")
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
            threshold = _extract_numeric_value(query, r"score\\s*>=\\s*(\\d+(?:\\.\\d+)?)")
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
            window = _extract_numeric_value(query, r"(\\d+)[- ]point moving average")
            output = []
            for index in range(len(prices) - int(window) + 1):
                chunk = prices[index:index + int(window)]
                output.append(round(sum(chunk) / len(chunk), 4))
            return output

        if ("json lines" in lowered or "read [" in lowered or "records with" in lowered) and ("return sum" in lowered or "sum " in lowered or "total " in lowered or "total field" in lowered):
            lines = _extract_first_list(query)
            field_match = re.search(
                r"(?:total field|return sum|sum|field|total)\\s+([a-zA-Z_][a-zA-Z0-9_]*)",
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
    '''
).strip()


_URL_TIME_SOLVER = dedent(
    '''
    def solve_url_time_query(query: str):
        lowered = query.lower()
        quoted = _extract_quoted_strings(query)

        if "query parameter names" in lowered or "query keys" in lowered:
            if not quoted:
                raise ValueError("Expected quoted URL")
            url = quoted[0]
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return sorted(params.keys())

        if "interval in minutes" in lowered or "difference in minutes" in lowered or "minute interval" in lowered:
            timestamps = quoted if len(quoted) >= 2 else _extract_first_list(query)
            start = datetime.fromisoformat(str(timestamps[0]).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(timestamps[1]).replace("Z", "+00:00"))
            return int((end - start).total_seconds() / 60)

        raise ValueError("Unsupported url/time query")
    '''
).strip()


_FALLBACK_SOLVER = dedent(
    '''
    def solve_any_query(query: str):
        """Handle benchmark-style text, list, structured-data, pipeline, and URL/time tasks."""
        handlers = (
            solve_text_query,
            solve_number_query,
            solve_structured_query,
            solve_pipeline_query,
            solve_url_time_query,
        )
        last_error = None
        for handler in handlers:
            try:
                return handler(query)
            except ValueError as exc:
                last_error = exc
        raise ValueError(str(last_error or "Unsupported query"))
    '''
).strip()


def _build_query_schema(name: str, description: str, source_code: str, tool_id: str) -> ToolSchema:
    return ToolSchema(
        tool_id=tool_id,
        name=name,
        description=description,
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Natural-language task to execute",
                required=True,
            )
        ],
        source_code=source_code,
        json_schema={
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language task to execute",
                    }
                },
                "required": ["query"],
            },
        },
    )


def _compose_source(public_name: str, description: str, solver_blocks: list[str], target_solver: str) -> str:
    public_wrapper = dedent(
        f'''
        def {public_name}(query: str):
            """{description}"""
            return {target_solver}(query)
        '''
    ).strip()
    return "\n\n\n".join([_COMMON_QUERY_HELPERS, *solver_blocks, public_wrapper]).strip() + "\n"


def default_tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "tool_id": "autoforge-text-basic-v1",
            "name": "text_basic_query_tool",
            "description": "Solve string reversal, vowel counting, title case, phone cleanup, and token frequency tasks.",
            "keywords": ["text", "string", "vowel", "reverse", "title case", "phone", "token frequency"],
            "examples": [
                "Count vowels in the string 'AutoForge'",
                "Reverse the text 'streamlit'",
                "Find top 2 frequent tokens in 'a b c a b a'",
            ],
            "source_code": _compose_source(
                "text_basic_query_tool",
                "Solve string reversal, vowel counting, title case, phone cleanup, and token frequency tasks.",
                [_TEXT_SOLVER],
                "solve_text_query",
            ),
        },
        {
            "tool_id": "autoforge-number-list-v1",
            "name": "number_list_query_tool",
            "description": "Solve sorting, averaging, deduplication, rounded sums, and byte-conversion tasks.",
            "keywords": ["list", "numbers", "average", "mean", "sort", "order", "ascending", "deduplicate", "first occurrences", "sum", "add", "bytes", "megabytes"],
            "examples": [
                "Sort numbers [5,1,9,2] ascending",
                "Order [5,1,9,2] ascending",
                "Compute average of [10,20,30,40]",
                "Convert 1048576 bytes to megabytes with 2 decimals",
            ],
            "source_code": _compose_source(
                "number_list_query_tool",
                "Solve sorting, averaging, deduplication, rounded sums, and byte-conversion tasks.",
                [_NUMBER_SOLVER],
                "solve_number_query",
            ),
        },
        {
            "tool_id": "autoforge-structured-data-v1",
            "name": "structured_data_query_tool",
            "description": "Solve dict, JSON, grouping, filtering, and category aggregation tasks.",
            "keywords": ["json", "dict", "keys", "alphabetically", "grouping", "filter rows", "score", "return names", "list names", "output names", "aggregate by category", "category totals", "contains key"],
            "examples": [
                "Extract keys from object {'name':'Ada','age':20} sorted alphabetically",
                "Given list [{'x':1},{'x':3}], sum field x",
                "Filter rows where score >= 80 and return names",
                "Compute category totals for rows with cat and amt",
                "Group words ['apple','ape','banana'] by first letter",
            ],
            "source_code": _compose_source(
                "structured_data_query_tool",
                "Solve dict, JSON, grouping, filtering, and category aggregation tasks.",
                [_STRUCTURED_SOLVER],
                "solve_structured_query",
            ),
        },
        {
            "tool_id": "autoforge-pipeline-v1",
            "name": "pipeline_query_tool",
            "description": "Solve CSV, JSONL, aggregation, moving-average, and multi-step pipeline tasks.",
            "keywords": ["csv", "jsonl", "moving average", "pipeline", "aggregate counts", "descending pairs", "null filtering", "drop null", "increase price", "join names"],
            "examples": [
                "From rows [{'item':'A','price':10}], increase price by 20%",
                "Given rows [{'v':1},{'v':null},{'v':3}], drop null v and return mean",
                "Read JSON lines ['{\"x\":1}','{\"x\":2}'], keep valid x records and return sum x",
            ],
            "source_code": _compose_source(
                "pipeline_query_tool",
                "Solve CSV, JSONL, aggregation, moving-average, and multi-step pipeline tasks.",
                [_PIPELINE_SOLVER],
                "solve_pipeline_query",
            ),
        },
        {
            "tool_id": "autoforge-url-time-v1",
            "name": "url_time_query_tool",
            "description": "Solve URL query-parameter and timestamp-interval tasks.",
            "keywords": ["url", "query parameters", "timestamp", "minutes", "iso time"],
            "examples": [
                "Parse URL 'https://example.com/path?a=1&b=2' and return query parameter names sorted",
                "Given ISO timestamps ['2025-01-01T00:00:00Z','2025-01-01T01:30:00Z'], return interval in minutes",
            ],
            "source_code": _compose_source(
                "url_time_query_tool",
                "Solve URL query-parameter and timestamp-interval tasks.",
                [_URL_TIME_SOLVER],
                "solve_url_time_query",
            ),
        },
    ]


def default_tool_schemas() -> list[tuple[ToolSchema, dict[str, Any]]]:
    tools: list[tuple[ToolSchema, dict[str, Any]]] = []
    for spec in default_tool_specs():
        tool = _build_query_schema(
            name=spec["name"],
            description=spec["description"],
            source_code=spec["source_code"],
            tool_id=spec["tool_id"],
        )
        tools.append(
            (
                tool,
                {
                    "created_at": "seeded",
                    "keywords": spec["keywords"],
                    "examples": spec["examples"],
                    "seeded": True,
                    "tool_origin": "seeded",
                    "tool_status": "active",
                },
            )
        )
    return tools


def fallback_solver_schema() -> ToolSchema:
    source_code = _compose_source(
        "benchmark_fallback_query_tool",
        "Handle benchmark-style text, list, structured-data, pipeline, and URL/time tasks.",
        [_TEXT_SOLVER, _NUMBER_SOLVER, _STRUCTURED_SOLVER, _PIPELINE_SOLVER, _URL_TIME_SOLVER, _FALLBACK_SOLVER],
        "solve_any_query",
    )
    return _build_query_schema(
        name="benchmark_fallback_query_tool",
        description="Handle benchmark-style text, list, structured-data, pipeline, and URL/time tasks.",
        source_code=source_code,
        tool_id="autoforge-fallback-query-v1",
    )


def _expected_seed_metadata(tool: ToolSchema, metadata_extra: dict[str, Any], existing_created_at: str | None = None) -> dict[str, Any]:
    metadata = {
        "metadata_version": 1,
        "tool_id": tool.tool_id,
        "name": tool.name,
        "description": tool.description,
        "created_at": existing_created_at or "seeded",
        "schema_file": "schema.json",
        "source_file": "tool.py",
        "readme_file": "README.md",
        "requirements_file": "requirements.txt",
        "example_input_file": "example_input.json",
        "imports": ["ast", "collections", "csv", "datetime", "io", "re", "urllib"],
        "language": "python",
        "tool_origin": "seeded",
        "tool_status": "active",
    }
    metadata.update(metadata_extra)
    return metadata


def _seed_bundle_current(bundle_path: Path, tool: ToolSchema, metadata_extra: dict[str, Any]) -> bool:
    tool_path = bundle_path / "tool.py"
    schema_path = bundle_path / "schema.json"
    metadata_path = bundle_path / "metadata.json"
    if not tool_path.exists() or not schema_path.exists() or not metadata_path.exists():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if metadata.get("tool_id") != tool.tool_id or not metadata.get("seeded"):
        return False
    if tool_path.read_text(encoding="utf-8") != f"{tool.source_code.rstrip()}\n":
        return False
    if schema != tool.json_schema:
        return False
    expected = _expected_seed_metadata(tool, metadata_extra, existing_created_at=metadata.get("created_at"))
    return metadata == expected


def ensure_default_skill_bundles(base_dir: str = BACKEND_SKILLS_DIR) -> list[Path]:
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for tool, metadata_extra in default_tool_schemas():
        bundle_path = base_path / tool.name
        if bundle_path.exists():
            metadata_path = bundle_path / "metadata.json"
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                except Exception:
                    metadata = {}
                if metadata.get("seeded") or metadata.get("tool_id") == tool.tool_id:
                    if _seed_bundle_current(bundle_path, tool, metadata_extra):
                        continue
                    shutil.rmtree(bundle_path)
                else:
                    continue
        created.append(create_skill_bundle(tool, base_dir=str(base_path), metadata_extra=metadata_extra))
    return created
