# AutoForge Benchmark Dataset

## Overview

This folder stores the benchmark used for evaluating:

- correctness
- latency
- TRR (Tool Reuse Rate)

Files:

- `dataset.json`: benchmark samples
- `dataset_schema.json`: JSON schema for validation
- generated via `scripts/generate_benchmark_dataset.py`

## Sample Format

Each item in `dataset.json` follows:

- `sample_id`: `L{difficulty}_{index}` (e.g. `L2_003`)
- `difficulty`: integer in `[1, 4]`
- `query`: canonical user query
- `paraphrases`: 3-5 equivalent variants
- `expected_output`: ground-truth output
- `expected_output_type`: `exact` | `numeric` | `contains`
- `tool_family`: capability tag (for grouped analysis)
- `notes`: optional

## Curation Guideline

Current dataset contains **80 canonical queries** with 3 paraphrases each and balanced difficulty buckets:

- L1: 20
- L2: 20
- L3: 20
- L4: 20

If you want to extend it further for a final report:

1. Keep 60-100 canonical queries for the project report scope.
2. Keep 3-5 paraphrases per query.
3. Balance by difficulty level.
4. Keep deterministic expected outputs where possible.
5. Regenerate with `scripts/generate_benchmark_dataset.py` so IDs and bucket counts stay consistent.

## Validation

Use the dataset tools before running large experiments:

```bash
python scripts/benchmark_dataset_tools.py validate
python scripts/benchmark_dataset_tools.py stats
```
