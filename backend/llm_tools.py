from __future__ import annotations

import json
import re

from shared.llm_factory import get_llm
from shared.schemas import ToolSchema


def llm_verify_tool_matches_query(query: str, tool: ToolSchema) -> bool:
    """Second-stage check: reduce false-positive RAG retrieval (proposal)."""
    llm = get_llm()
    prompt = (
        "You are a strict router for Python tools.\n"
        f"User request:\n{query}\n\n"
        f"Candidate tool name: {tool.name}\n"
        f"Candidate tool description:\n{tool.description}\n\n"
        "Can this specific tool correctly fulfill the user's request as stated? "
        "Answer with exactly YES or NO, nothing else."
    )
    text = (llm.invoke(prompt).content or "").strip().upper()
    return text.startswith("YES")


def extract_invocation_payload(query: str, tool: ToolSchema) -> dict:
    """Lightweight parameter extraction for fast-path dispatch."""
    llm = get_llm()
    schema_hint = json.dumps(tool.json_schema, ensure_ascii=False, indent=2)
    prompt = (
        "Extract arguments to call the Python function from the user message.\n"
        f"Function name: {tool.name}\n"
        "Return ONLY a single JSON object. Keys must match the tool parameter names.\n"
        f'Include the key "__function_name" with string value "{tool.name}".\n'
        "Use JSON types: numbers for int/float, strings for str, true/false for bool.\n"
        "If the user message does not specify a value, use a reasonable default.\n\n"
        f"JSON Schema (OpenAI-style):\n{schema_hint}\n\n"
        f"User message:\n{query}\n"
    )
    raw = (llm.invoke(prompt).content or "").strip()
    cleaned = raw
    if "```" in cleaned:
        m = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM did not return a JSON object")
    data.setdefault("__function_name", tool.name)
    return data
