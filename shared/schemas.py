from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PathType(str, Enum):
    FAST = "fast"
    SLOW = "slow"


class QueryStrategy(str, Enum):
    FULL = "full"
    NO_RETRIEVAL = "no_retrieval"
    REGISTRY_ONLY = "registry_only"
    AGENT = "agent"


class ForgeRequest(BaseModel):
    query: str = Field(..., description="User request to be forged into a tool")


class PlannerOutput(BaseModel):
    steps: list[str] = Field(default_factory=list)
    suggested_function_name: str = Field(..., description="Snake_case function name")


class CoderOutput(BaseModel):
    source_code: str
    function_name: Optional[str] = None


class VerifierOutput(BaseModel):
    success: bool
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time_ms: Optional[float] = None
    failure_type: Optional[str] = None
    cases: list[dict[str, Any]] = Field(default_factory=list)


class ToolParameter(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True


class ToolSchema(BaseModel):
    tool_id: str
    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    source_code: str
    json_schema: dict[str, Any] = Field(default_factory=dict)


class ForgeResult(BaseModel):
    status: Literal["success", "failed"]
    tool: Optional[ToolSchema] = None
    error: Optional[str] = None
    attempts: Optional[int] = None
    trace_id: Optional[str] = None
    log_path: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
    strategy: QueryStrategy = QueryStrategy.FULL
    skip_llm_match_verify: bool = False
    explain_only: bool = Field(
        default=False,
        description="If true, return retrieval candidates and planned invocation without executing any tool.",
    )
    dry_run: bool = Field(
        default=False,
        description="Alias of explain_only. If true, do not execute any tool.",
    )


class QueryResponse(BaseModel):
    path_taken: PathType
    result: Any = None
    total_latency_ms: Optional[float] = None
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    strategy: QueryStrategy = QueryStrategy.FULL
    reused_existing_tool: bool = False
    retrieval_latency_ms: Optional[float] = None
    forge_latency_ms: Optional[float] = None
    execution_latency_ms: Optional[float] = None
    search_score: Optional[float] = None
    retrieval_trace: list[dict[str, Any]] = Field(default_factory=list)
    explain: Optional[dict[str, Any]] = None
    forge_trace_id: Optional[str] = None
    forge_log_path: Optional[str] = None
    forge_summary: Optional[dict[str, Any]] = None
    failure_type: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    total_tools: int
    retrieval_backend: str
    similarity_threshold: float = 0.0
    available_strategies: list[QueryStrategy] = Field(default_factory=list)


class ToolSummary(BaseModel):
    tool_id: str
    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    metadata_version: Optional[int] = None
    tool_origin: Optional[str] = None
    tool_status: Optional[str] = None


class ToolListResponse(BaseModel):
    total: int
    tools: list[ToolSummary] = Field(default_factory=list)


class BenchmarkSample(BaseModel):
    sample_id: str
    difficulty: int
    query: str
    paraphrases: list[str] = Field(default_factory=list)
    expected_output: Any
    expected_output_type: Literal["exact", "numeric", "contains"]
    tool_family: str


class MatchVerdict(BaseModel):
    matched: bool
    reason: Optional[str] = None
