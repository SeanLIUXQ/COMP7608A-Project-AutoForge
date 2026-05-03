from __future__ import annotations

import ast
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from shared.schemas import CoderOutput, ToolParameter, ToolSchema


_TYPE_MAP = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
    "dict": "object",
    "list": "array",
}
_MISSING = object()


def _annotation_to_json_type(node: Optional[ast.AST]) -> str:
    if node is None:
        return "string"
    if isinstance(node, ast.Name):
        if node.id == "None":
            return "null"
        return _TYPE_MAP.get(node.id, "string")
    if isinstance(node, ast.Constant) and node.value is None:
        return "null"
    if isinstance(node, ast.Attribute):
        return _TYPE_MAP.get(node.attr, "string")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left_type = _annotation_to_json_type(node.left)
        right_type = _annotation_to_json_type(node.right)
        return right_type if left_type == "null" else left_type
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        base = node.value.id
        if base in {"list", "List", "Sequence", "tuple", "Tuple"}:
            return "array"
        if base in {"dict", "Dict", "Mapping"}:
            return "object"
        if base in {"Optional", "Union"}:
            if isinstance(node.slice, ast.Tuple):
                for elt in node.slice.elts:
                    if isinstance(elt, ast.Name) and elt.id == "None":
                        continue
                    return _annotation_to_json_type(elt)
            return "string"
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
        base = node.value.attr
        if base in {"list", "List", "Sequence", "tuple", "Tuple"}:
            return "array"
        if base in {"dict", "Dict", "Mapping"}:
            return "object"
        if base in {"Optional", "Union"}:
            return _annotation_to_json_type(node.slice)
    return "string"


def _extract_function(source_code: str) -> Optional[ast.FunctionDef]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node
    return None


def run_packager(coder_output: CoderOutput) -> ToolSchema:
    func = _extract_function(coder_output.source_code)
    function_name = coder_output.function_name or "generated_tool"
    description = "Auto-generated tool"
    parameters: list[ToolParameter] = []
    required: list[str] = []

    if func:
        function_name = func.name or function_name
        docstring = ast.get_docstring(func)
        if docstring:
            description = docstring.strip().splitlines()[0]

        args = [arg for arg in func.args.args if arg.arg != "self"]
        defaults_offset = len(args) - len(func.args.defaults)

        for index, arg in enumerate(args):
            default_node = func.args.defaults[index - defaults_offset] if index >= defaults_offset else _MISSING
            json_type = _annotation_to_json_type(arg.annotation)
            is_required = default_node is _MISSING
            parameters.append(
                ToolParameter(
                    name=arg.arg,
                    type=json_type,
                    required=is_required,
                )
            )
            if is_required:
                required.append(arg.arg)

        for arg, default_node in zip(func.args.kwonlyargs, func.args.kw_defaults):
            json_type = _annotation_to_json_type(arg.annotation)
            is_required = default_node is None
            parameters.append(
                ToolParameter(
                    name=arg.arg,
                    type=json_type,
                    required=is_required,
                )
            )
            if is_required:
                required.append(arg.arg)

    json_schema = {
        "name": function_name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                param.name: {
                    "type": param.type,
                    "description": param.description or "",
                }
                for param in parameters
            },
            "required": required,
        },
    }

    return ToolSchema(
        tool_id=str(uuid.uuid4()),
        name=function_name,
        description=description,
        parameters=parameters,
        source_code=coder_output.source_code,
        json_schema=json_schema,
    )


def _safe_dir_name(name: str) -> str:
    cleaned = []
    for ch in name:
        if (ch.isascii() and ch.isalnum()) or ch in {"_", "-"}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    result = "".join(cleaned).strip("_")
    return result or "tool"


def _extract_imports_from_source(source_code: str) -> list[str]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return sorted(imports)


def _build_example_input(tool: ToolSchema) -> dict:
    type_defaults = {
        "integer": 1,
        "number": 1.0,
        "string": "example",
        "boolean": True,
        "object": {},
        "array": [],
    }
    payload: dict = {"__function_name": tool.name}
    for param in tool.parameters:
        payload[param.name] = type_defaults.get(param.type, "example")
    return payload


def _build_readme(tool: ToolSchema, imports: list[str]) -> str:
    params = "\n".join(
        f"- {param.name} ({param.type}){' [required]' if param.required else ''}"
        for param in tool.parameters
    )
    if not params:
        params = "- (no parameters)"
    imports_line = ", ".join(imports) if imports else "stdlib only / none detected"
    return (
        f"# {tool.name}\n\n"
        f"{tool.description}\n\n"
        "## Parameters\n"
        f"{params}\n\n"
        "## Imports\n"
        f"{imports_line}\n\n"
        "## Usage\n"
        "Use `example_input.json` as a starting point for invocation.\n"
    )


def create_skill_bundle(
    tool: ToolSchema,
    base_dir: str = "skills",
    metadata_extra: dict[str, Any] | None = None,
) -> Path:
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_dir_name(tool.name)
    bundle_path = base_path / safe_name
    if bundle_path.exists():
        bundle_path = base_path / f"{safe_name}__{tool.tool_id[:8]}"
    bundle_path.mkdir(parents=True, exist_ok=True)

    tool_path = bundle_path / "tool.py"
    schema_path = bundle_path / "schema.json"
    meta_path = bundle_path / "metadata.json"
    readme_path = bundle_path / "README.md"
    requirements_path = bundle_path / "requirements.txt"
    example_path = bundle_path / "example_input.json"

    imports = _extract_imports_from_source(tool.source_code)

    tool_path.write_text(f"{tool.source_code.rstrip()}\n", encoding="utf-8")
    schema_path.write_text(json.dumps(tool.json_schema, indent=2, ensure_ascii=False), encoding="utf-8")
    readme_path.write_text(_build_readme(tool, imports), encoding="utf-8")
    requirements_path.write_text(
        "# AutoForge skill requirements\n"
        "# Add third-party packages if the tool imports them.\n",
        encoding="utf-8",
    )
    example_path.write_text(
        json.dumps(_build_example_input(tool), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    created_at = (
        str(metadata_extra.get("created_at"))
        if metadata_extra and metadata_extra.get("created_at")
        else datetime.now(timezone.utc).isoformat()
    )
    metadata = {
        "metadata_version": 1,
        "tool_id": tool.tool_id,
        "name": tool.name,
        "description": tool.description,
        "created_at": created_at,
        "schema_file": "schema.json",
        "source_file": "tool.py",
        "readme_file": "README.md",
        "requirements_file": "requirements.txt",
        "example_input_file": "example_input.json",
        "imports": imports,
        "language": "python",
        # Tool lifecycle labels (used by backend listing + trace/debug views).
        # Keep boolean flags like `seeded` / `forged` if present for backwards compatibility.
        "tool_origin": "unknown",
        "tool_status": "active",
    }
    if metadata_extra:
        metadata.update(metadata_extra)
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return bundle_path
