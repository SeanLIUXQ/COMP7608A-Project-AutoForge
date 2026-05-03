from __future__ import annotations

import json
import re
from pathlib import Path

from shared.llm_factory import get_llm
from shared.schemas import ForgeRequest, PlannerOutput


def _load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _to_snake_case(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    if not words:
        return "generated_tool"
    name = "_".join(words[:8])
    if name[0].isdigit():
        name = f"tool_{name}"
    if not name.isidentifier():
        name = "generated_tool"
    return name[:60]


def _normalize_plan(data: dict, fallback_query: str) -> PlannerOutput:
    steps = data.get("steps")
    if isinstance(steps, list):
        steps = [str(step) for step in steps if step]
    else:
        steps = []
    suggested = data.get("suggested_function_name")
    if not isinstance(suggested, str) or not suggested:
        suggested = _to_snake_case(fallback_query)
    elif not suggested.isidentifier():
        suggested = _to_snake_case(suggested)
    return PlannerOutput(steps=steps, suggested_function_name=suggested)


def run_planner(request: ForgeRequest) -> PlannerOutput:
    llm = get_llm()
    system_prompt = _load_prompt("planner_system.txt")
    prompt = f"{system_prompt}\n\nUser request: {request.query}"
    response = llm.invoke(prompt)
    try:
        data = _extract_json(response.content)
        if not isinstance(data, dict):
            raise ValueError("Planner output is not a JSON object")
        return _normalize_plan(data, request.query)
    except Exception:
        fallback = {
            "steps": [
                "Understand the request",
                "Define inputs and outputs",
                "Implement the function",
                "Return the result",
            ],
            "suggested_function_name": _to_snake_case(request.query),
        }
        return _normalize_plan(fallback, request.query)
