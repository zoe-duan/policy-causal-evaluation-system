---
name: dml-doubly-robust
description: Use for Double/Debiased Machine Learning, AIPW, doubly robust estimation, cross-fitting, high-dimensional covariates, and nuisance model diagnostics.
---


## Goal

Use causal ML for valid treatment effect estimation when identification is based on observed covariates and overlap.

## Workflow

1. Confirm estimand and identification: DML does not solve unobserved confounding.
2. Define Y, D, X, optional W/controls, clusters, sample weights.
3. Choose score: PLR, IRM, AIPW/DR, IV-DML if instrument exists.
4. Use cross-fitting. Do not train nuisance models and estimate effects on the same fold.
5. Report nuisance learners, folds, random seeds, overlap diagnostics.
6. Run learner sensitivity: linear, random forest, boosting or other ML.
7. Report effect estimate, standard error, confidence interval, and assumptions.

## Local demo

```bash
python scripts/run_demo_analysis.py
```

## Guardrails

- High prediction accuracy is not equal to causal validity.
- Check extreme propensity scores.
- Avoid post-treatment covariates.

