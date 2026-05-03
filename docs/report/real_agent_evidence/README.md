# Liu Xinquan Real Agent Evidence Summary

Primary source report: `evaluation\results\agent_demo_report_agent_20260502_074909.json`

This folder contains the final **50-trial real LLM agent evidence** for Liu Xinquan's report section. The experiment uses DeepSeek `deepseek-v4-pro` and Docker sandbox verification to demonstrate the cold-forge and warm-reuse behavior of AutoForge under real LLM calls.

| Metric | Value |
|---|---:|
| model | deepseek-v4-pro |
| sandbox_backend | docker |
| docker_image | autoforge-sandbox:latest |
| base_case_count | 10 |
| repeats | 5 |
| total_trials | 50 |
| cold_forge_success_count | 50 |
| cold_forge_success_rate | 1.0 |
| warm_success_count | 46 |
| warm_success_rate | 0.92 |
| warm_reuse_count | 46 |
| warm_reuse_rate | 0.92 |
| duration_minutes | 74.85 |

## Evidence Files

- `agent_reports/agent_demo_report_agent_20260502_074909_50trials.json`: final 50-trial real DeepSeek agent run.
- `agent_reports/agent_demo_report_agent_20260502_054643.json`: earlier 10-trial pilot run.
- `agent_reports/smoke_agent_demo_report_agent_20260502_042536.json`: one-case smoke run.
- `agent_demo_summary.json`: compact JSON summary of the final 50-trial run.
- `agent_demo_case_table.csv`: trial-level table for report writing.
- `figures/agent_demo_trials_flat.csv`: flattened raw rows used for plotting.
- `figures/agent_demo_repeat_summary.csv`: repeat-level summary used for plotting.
- `figures/agent_demo_cumulative_rates.png`: cumulative cold/warm/reuse curves.
- `figures/agent_demo_latency_trend.png`: cold vs warm latency trend.
- `figures/agent_demo_family_rates.png`: success and reuse rates by task family.
- `figures/agent_demo_latency_distribution.png`: latency distribution box plot.
- `docker_sandbox/docker_sandbox_verification.json`: Docker sandbox safety check.
- `forge_logs/liu_xinquan_real_agent_50/`: final 50-trial forge traces and verification logs.
- `generated_tools/skills_report_llm_50/`: generated tool bundles from the final run.
- `screenshots/chat_page.png`: live Streamlit chat page.
- `screenshots/dashboard_agent_report.png`: dashboard backend and tool-catalog evidence.
- `screenshots/tool_browser_forged_tools.png`: generated tool browser evidence.
- `screenshots/fastapi_openapi.png`: live FastAPI documentation evidence.
- `screenshots/frontend_home.png`: Streamlit home page evidence.

## Docker Sandbox Check

| Check | Result | Evidence |
|---|---|---|
| Safe execution | Passed | `safe_add` returned `5`. |
| Unsafe file access | Rejected | `open()` returned `unsafe_call`. |
| Unsafe import | Rejected | `os` returned `unsafe_import`. |

## Repeat Summary

| Repeat | Trials | Cold Forge | Warm Success | Warm Reuse |
|---:|---:|---:|---:|---:|
| 1 | 10 | 1.0 | 0.9 | 0.9 |
| 2 | 10 | 1.0 | 1.0 | 0.9 |
| 3 | 10 | 1.0 | 0.9 | 1.0 |
| 4 | 10 | 1.0 | 0.8 | 0.8 |
| 5 | 10 | 1.0 | 1.0 | 1.0 |

## Family Summary

| Family | Trials | Cold Forge | Warm Success | Warm Reuse |
|---|---:|---:|---:|---:|
| category_aggregation | 5 | 1.0 | 1.0 | 1.0 |
| csv_text | 5 | 1.0 | 0.6 | 0.8 |
| json_rows | 5 | 1.0 | 1.0 | 1.0 |
| jsonl | 5 | 1.0 | 0.6 | 0.6 |
| list | 10 | 1.0 | 1.0 | 0.9 |
| moving_average | 5 | 1.0 | 1.0 | 1.0 |
| string | 10 | 1.0 | 1.0 | 1.0 |
| url | 5 | 1.0 | 1.0 | 1.0 |

## Notes

The 50 real agent trials demonstrate real LLM-backed cold forging and warm reuse under time and token-budget constraints. They should be interpreted as evidence for the agent demo path, not as a replacement for the full 320-query backend benchmark. Future work should compare multiple LLM providers and model families within the same AutoForge workflow.
