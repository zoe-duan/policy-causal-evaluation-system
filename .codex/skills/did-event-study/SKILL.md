---
name: did-event-study
description: Use for panel policy evaluations with treated/control units before and after treatment, including DID, event study, pre-trend checks, dynamic effects, and staggered adoption warnings.
---


## Goal

Design and implement DID/event-study analysis for policy evaluation.

## When to use

- Units observed before and after policy.
- Treated and comparison units exist.
- Treatment timing is known.
- Counterfactual assumption is parallel trends or a defensible variant.

## Workflow

1. Confirm unit, time, treatment timing, outcome, and comparison group.
2. Specify estimand: ATT or dynamic ATT.
3. Check whether adoption is simultaneous or staggered.
4. If staggered, warn against naive TWFE as sole estimator when heterogeneity is likely.
5. Define event-time leads/lags and reference period.
6. Run diagnostics: pre-trends, placebo dates, placebo outcomes, composition changes.
7. Cluster standard errors at assignment unit or higher.
8. Create outputs: coefficient table, event-study plot, narrative diagnostics.

## Minimal Python path

```bash
python scripts/run_demo_analysis.py
```

For custom data, adapt `src/causal_policy_system/estimators.py`.

## Output standard

State results as: “Under the maintained parallel trends/no anticipation assumptions...”.

