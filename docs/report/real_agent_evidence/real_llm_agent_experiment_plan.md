# Real LLM Agent Experiment Plan

Last updated: 2026-05-02

## 1. Recommended Plan

The final report uses the following evidence design:

1. **320-query live backend benchmark**: run `full,no_retrieval,registry_only` as the main quantitative system comparison.
2. **50 real LLM agent trials**: run `run_agent_demo_cases.py --limit 10 --repeats 5`, repeating 10 representative demo cases for 5 rounds as stability evidence for the LLM cold forge -> warm reuse process.
3. **No default full 320-query `strategy=agent` run**: run it only as an extension when budget, time, and API stability are sufficient.

This balances three requirements:

- The main system results still use a 320-query benchmark.
- The LLM agent evidence comes from a real API rather than a mock.
- Cost and runtime remain manageable, and failures are easier to inspect through forge logs.

## 2. Why 50 Trials Instead of 10 or a Full 320-Query Agent Benchmark

`agents/demo_cases.json` currently contains 10 representative task cases:

- string reverse
- vowel count
- sort numbers
- deduplicate list
- JSON row filtering
- CSV text parsing
- JSONL sum
- moving average
- category aggregation
- URL query key extraction

Five cases would provide minimal evidence, but the coverage would be too narrow and would mostly focus on L1/L2 tasks. Ten cases cover all demo families, and repeating them for five rounds produces 50 real trials. This scale is more suitable for report tables, plots, and stability analysis. A full 320-query `strategy=agent` benchmark would be stronger, but it greatly increases cost, runtime, rate-limit exposure, and sensitivity to occasional model failures. Therefore, it is not recommended as the default required run.

## 3. DeepSeek Cost Estimate

The formal real LLM agent demo uses the DeepSeek Pro model:

```text
LLM_PROVIDER=deepseek
LLM_MODEL_NAME=deepseek-v4-pro
```

According to the DeepSeek official pricing page, `deepseek-v4-pro` supports 1M context, JSON output, and tool calls. As of 2026-05-02, the listed discounted API prices were:

| Token Type | Price |
|---|---:|
| Input cache miss | USD 0.435 / 1M tokens |
| Input cache hit | USD 0.003625 / 1M tokens |
| Output | USD 0.87 / 1M tokens |

Source: DeepSeek Models & Pricing  
https://api-docs.deepseek.com/quick_start/pricing

The pricing should be treated as a date-specific estimate rather than a permanent price. AutoForge calls at least the planner and coder for each cold forge case. If verification fails, the coder may retry up to `MAX_FORGE_RETRIES`. The warm reuse stage may also call the payload-extraction LLM to convert natural-language requests into tool parameters.

Conservative estimate:

| Experiment Scale | Estimated LLM Calls | Estimated Cost | Suggested Use |
|---|---:|---:|---|
| 1 smoke test | 3-6 calls | < USD 0.03 | Validate key, network, prompts, and Docker sandbox |
| 5 demo cases | 15-30 calls | USD 0.03-0.10 | Minimal real-agent evidence |
| 10 demo cases | 30-60 calls | USD 0.06-0.20 | Single-round pilot |
| 50 repeated demo trials | 150-300 calls | USD 0.30-1.00 | Recommended final-report setting |
| 32-sample agent benchmark | 96-200 calls | USD 0.20-1.00 | Optional extension |
| Full 320-query agent benchmark | 960-2000+ calls | USD 2.00-15.00+ | Extended experiment with high runtime |

Actual cost varies with retry count, generated code length, cache hit rate, and failure retries. The current scripts do not record token usage per API call, so the cost should be reported as an estimate range, not an exact bill.

## 4. Runtime Estimate

Assuming 20-90 seconds per cold forge case:

| Experiment Scale | Estimated Runtime |
|---|---:|
| 1 smoke test | 1-3 minutes |
| 5 demo cases | 5-15 minutes |
| 10 demo cases | 10-30 minutes |
| 50 repeated demo trials | 60-120 minutes |
| 32-sample agent benchmark | 30-90 minutes |
| Full 320-query agent benchmark | 5-12 hours or longer |

Runtime can increase with retries, slower network responses, or rate limits. The recommended report setting is therefore 50 repeated demo trials, together with forge logs, warm-reuse evidence, and matplotlib figures.

## 5. Recommended Commands

Load `.env` into the current PowerShell process:

```powershell
cd <path-to-cloned-repository>
$env:PYTHONPATH='.'

Get-Content .env | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object {
  $name, $value = $_ -split '=', 2
  if ($name -and $value) {
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process")
  }
}

$env:LLM_PROVIDER='deepseek'
$env:LLM_MODEL_NAME='deepseek-v4-pro'
$env:SANDBOX_BACKEND='docker'
$env:SANDBOX_DOCKER_IMAGE='autoforge-sandbox:latest'
```

Confirm that the key is loaded:

```powershell
python -c "import os; print('provider=', os.getenv('LLM_PROVIDER')); print('model=', os.getenv('LLM_MODEL_NAME')); print('has_key=', bool(os.getenv('DEEPSEEK_API_KEY')))"
```

Run a one-case smoke test first:

```powershell
$env:AUTOFORGE_FORGE_LOG_DIR='data/forge_logs/liu_xinquan_real_agent_smoke'
docker build -t autoforge-sandbox:latest -f docker\Dockerfile.sandbox docker
python scripts\run_agent_demo_cases.py --limit 1 --skills-dir skills_report_llm
```

After the smoke test succeeds, run the formal 50 trials:

```powershell
$env:AUTOFORGE_FORGE_LOG_DIR='data/forge_logs/liu_xinquan_real_agent_final_v2'
python scripts\run_agent_demo_cases.py --limit 10 --repeats 5 --skills-dir skills_report_llm_50 --checkpoint-interval 5
```

Expected outputs:

- `evaluation/results/agent_demo_report_agent_*.json`
- `data/forge_logs/*.json`
- generated forged tools under `skills_report_llm/`

The formal run uses Docker as the execution backend. The report should explicitly mention:

- Docker image: `autoforge-sandbox:latest`
- Sandbox backend: `SANDBOX_BACKEND=docker`
- Evidence folder: `docs/report/real_agent_evidence/`
- Docker safety checks: safe functions execute, while `open()` and `os` import are rejected and recorded as `unsafe_call` and `unsafe_import`

## 6. Reporting Wording

Recommended wording:

> We report the 320-query live backend benchmark as the main quantitative system comparison. Because forcing all 320 queries through the real LLM forge pipeline would be expensive and time-consuming, we evaluate the LLM agent separately on 50 real cold/warm trials, produced by repeating 10 representative demo cases for 5 rounds. Each cold query uses the real DeepSeek `deepseek-v4-pro` backed `strategy=agent` path, with generated code verified inside the Docker sandbox. Each warm query tests whether the generated tool can be reused through the registry/retrieval path.

Avoid the following claims:

- "10 agent demo cases are equivalent to the full 320-query agent benchmark."
- "The backend fallback success rate is the LLM agent success rate."
- "Mock agent demos are real LLM evidence."

## 7. Optional Extension

If the 50 repeated demo trials are complete and more quantitative evidence is needed, a 32-sample real agent experiment can be added. The current `evaluation.runner` does not directly support sampling, so this should not be described as a ready-made command in the report. A practical approach is to temporarily generate a small dataset, for example by sampling 8 canonical cases from each difficulty level, and then run `strategy=agent` on that dataset. The results should only be cited after actual `eval_report_backend_agent_*.json` files have been generated.

