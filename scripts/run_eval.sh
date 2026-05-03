#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-backend}"
STRATEGIES="${2:-full,no_retrieval,registry_only}"
BACKEND_URL="${3:-http://127.0.0.1:8000}"

if [[ "$MODE" == "backend" ]]; then
  python -m evaluation.runner --mode "$MODE" --strategies "$STRATEGIES" --backend-url "$BACKEND_URL"
else
  python -m evaluation.runner --mode "$MODE" --strategies "$STRATEGIES"
fi
