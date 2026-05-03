# AutoForge Benchmark Design

Last updated: 2026-05-01

## 1. Objective

The AutoForge benchmark evaluates three aspects of the system:

1. Correctness: whether the tool execution result matches the ground truth.
2. Efficiency: whether the Tool-RAG fast path reduces latency compared with the slow path.
3. Reuse: whether warm paraphrase queries can reuse an existing tool, measured by Tool Reuse Rate (TRR).

## 2. Dataset Scale

The benchmark dataset is stored at `evaluation/benchmark/dataset.json`.

| Difficulty | Canonical Samples | Paraphrases | Focus |
|---|---:|---:|---|
| L1 | 20 | 60 | Strings, lists, basic mathematics, and unit conversion |
| L2 | 20 | 60 | JSON, URLs, timestamps, table filtering, and text grouping |
| L3 | 20 | 60 | CSV-like text, JSONL, aggregation, moving averages, and multi-step processing |
| L4 | 20 | 60 | Longer inputs, complex filtering, aggregation, and multi-step ETL |

Overall:

- 80 canonical samples.
- 3 paraphrases per sample.
- `80 * (1 + 3) = 320` evaluation queries per strategy.

## 3. Schema

Each sample follows `evaluation/benchmark/dataset_schema.json`:

- `sample_id`: for example, `L1_001`.
- `difficulty`: from 1 to 4.
- `query`: the canonical cold query.
- `paraphrases`: three warm queries.
- `expected_output`: the ground-truth answer.
- `expected_output_type`: `exact`, `numeric`, or `contains`.
- `tool_family`: the task-family label.

## 4. Tool Families

The current benchmark covers 17 task families:

- `aggregation_pipeline`
- `csv_pipeline`
- `data_cleaning_pipeline`
- `datetime_ops`
- `json_processing`
- `jsonl_pipeline`
- `list_ops`
- `math_ops`
- `phone_cleanup`
- `string_ops`
- `table_filter`
- `text_etl_pipeline`
- `text_grouping`
- `text_stats`
- `timeseries_pipeline`
- `unit_conversion`
- `url_processing`

## 5. Recommended Evaluation Protocol

### Live Backend System Benchmark

The main system comparison uses:

```powershell
python -m evaluation.runner --mode backend --strategies full,no_retrieval,registry_only --backend-url http://127.0.0.1:8000
```

Strategy definitions:

- `full`: retrieve from the registry first; execute an existing tool on a confident match; otherwise use the slow path.
- `no_retrieval`: skip retrieval and directly use the slow path or deterministic fallback.
- `registry_only`: retrieve only and do not fall back; this measures registry coverage.

The default slow path uses deterministic fallback. Therefore, these results are live backend/system evidence, not LLM-generation evidence.

### Real LLM Agent Evidence

The final report should include separate real LLM agent evidence. The recommended plan is not to force the full 320-query benchmark through `strategy=agent`. Instead, AutoForge uses **50 repeated real agent trials** by repeating 10 representative demo cases for 5 rounds. The selected cases cover strings, lists, JSON rows, CSV, JSONL, moving averages, aggregation, URL parsing, and related task families:

```powershell
python scripts\run_agent_demo_cases.py --limit 10 --repeats 5 --skills-dir skills_report_llm_50 --checkpoint-interval 5
```

These results support the "cold forge -> warm reuse" claim:

- The cold query uses `strategy=agent` to show real LLM planning, code generation, verification, and packaging.
- The warm query uses `strategy=full` to test whether the generated tool can be reused through registry/retrieval.
- Outputs include `agent_demo_report_agent_*`, `data/forge_logs/*.json`, and `skills_report_llm/`.

If time and budget allow, the full 320-query LLM agent benchmark can be run as an extension:

```powershell
python -m evaluation.runner --mode backend --strategies agent --backend-url http://127.0.0.1:8000
```

`strategy=agent` forces each query through the real LLM forge pipeline. It is more expensive, slower, and affected by model stability and retry count, so it is not recommended as a required run unless time and budget are sufficient.

## 6. Metrics

- Success Rate: percentage of outputs that match the expected answer.
- Tool Reuse Rate / TRR: percentage of queries that reuse an existing tool.
- Error Rate: percentage of failed or unmatched executions.
- Latency: average latency for fast and slow paths.
- Speedup Ratio: `mean slow latency / mean fast latency`.
- Per-family Success: success rate grouped by `tool_family`.
- Failure Taxonomy: distribution of failure types.

## 7. Reporting Rules

- `mode=backend` means the actual backend was used, not a mock.
- `agent_demo_report_agent_*` can be used as representative real LLM agent generation evidence.
- `eval_report_backend_agent_*` should only be cited if the full 320-query agent benchmark has actually been run.
- `eval_report_mock_*` should not be used as main final-report evidence.
- Backend fallback results can be used as a baseline, but they should not be described as LLM-generated results.
- The recommended final-report structure is: use the 320-query live backend benchmark as the quantitative system comparison, and use the 50 repeated real agent trials as representative LLM generation stability evidence.
