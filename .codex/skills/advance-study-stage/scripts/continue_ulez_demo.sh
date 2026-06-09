#!/usr/bin/env bash
set -euo pipefail
python scripts/continue_study.py \
  --slug london-ulez-outer-london-2023 \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
