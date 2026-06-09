---
name: advance-study-stage
summary: Top-level orchestration for continuing an existing policy evaluation study from one workflow stage to the next.
description: Use this when the user says “继续”, “下一步”, “然后呢”, “推进到数据/估计/稳健性阶段”, “first-pass estimation”, or asks Codex to continue a study without writing a long prompt.
---

# Advance study stage

This skill converts a short user instruction into a deterministic workflow. Do **not** ask the user to write a long prompt.

## Trigger phrases

Use this skill when the user says things like:

- “然后呢”
- “继续 ULEZ demo”
- “继续这个研究”
- “推进到 first-pass estimation”
- “进入数据准备阶段”
- “先审查设计，缺数据就 demo data”
- “把这个研究继续往下跑”

## Required behavior

1. Locate the study under `studies/<slug>/`. If the user gives a slug, use it. If not, run status detection.
2. Run the top-level orchestrator, not a manually expanded prompt.
3. Always run the design/policy-fact gate before data or estimation.
4. Never fabricate real data. If the user permits demo data, generate only clearly marked `DEMO DATA`.
5. Never upgrade first-pass estimates into substantive causal claims.
6. Leave reusable artifacts under the study folder.

## Primary commands

Check status:

```bash
python scripts/continue_study.py --slug <slug> --status
```

Advance automatically to the recommended next stage:

```bash
python scripts/continue_study.py --slug <slug> --next-stage auto
```

Advance to first-pass estimation with demo data only if real data are missing:

```bash
python scripts/continue_study.py \
  --slug <slug> \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

Equivalent CLI wrapper:

```bash
python scripts/causal_policy_cli.py continue-study \
  --slug <slug> \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

## One-line interaction pattern

User should only need to say:

```text
继续 studies/<slug>，推进到 first-pass estimation。先做 go/no-go 审查；缺真实数据就生成明确标注的 demo data；不要输出真实因果结论。
```

Codex should respond by running the orchestrator and summarizing changed files, checks, and blocked gates.

## Outputs to inspect

- `workflow_state.json`
- `design_review.md`
- `data_sources.md`
- `data_readiness_check.md`
- `data/processed/analysis_panel.csv`
- `tables/event_study_results.csv`
- `estimation_report.md`
- `orchestrator_summary.md`
- `orchestrator_report.md`

## Stop conditions

Stop and explain the blocking issue when:

- `design_card.yaml` is missing or invalid;
- policy source register or policy extraction is missing;
- real data are missing and the user did not permit demo data;
- `analysis_panel.csv` lacks required fields;
- event-study sample has too few units or periods.
