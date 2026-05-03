from __future__ import annotations

import re
from pathlib import Path

from shared.llm_factory import get_llm
from shared.schemas import CoderOutput, PlannerOutput


def _load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


def _extract_code_block(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def run_coder(plan: PlannerOutput, previous_error: str | None = None) -> CoderOutput:
    llm = get_llm()
    system_prompt = _load_prompt("coder_system.txt")
    prompt = (
        f"{system_prompt}\n\nPlan JSON:\n{plan.model_dump_json()}\n\n"
        "Return only the code block."
    )
    if previous_error:
        prompt += (
            "\n\nThe previous verification attempt failed. Fix only the function implementation.\n"
            "Keep the exact requested function name and return one Python code block.\n"
            f"Verification feedback:\n{previous_error}\n"
        )

    response = llm.invoke(prompt)
    source_code = _extract_code_block(response.content)
    return CoderOutput(source_code=source_code, function_name=plan.suggested_function_name)
