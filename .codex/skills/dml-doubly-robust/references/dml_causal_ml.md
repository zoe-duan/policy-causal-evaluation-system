# Frontier Methods Notes

This file is a compact map, not a textbook.

## Double / Debiased Machine Learning

Use when treatment is not randomized but selection on rich observables is plausible. DML uses ML for nuisance functions and orthogonal scores so small nuisance errors do not dominate the target treatment effect. Requirements: overlap, pre-treatment covariates, sample splitting/cross-fitting, honest reporting of nuisance models.

Recommended artifacts:

- nuisance model spec
- cross-fitting folds
- overlap plot
- sensitivity to learners
- confidence interval and clustering choice

## Doubly Robust / AIPW

Combines propensity and outcome models. Useful as a robustness bridge between matching/weighting and regression. Beware extreme propensities.

## Generalized Random Forests and Causal Forests

Use for heterogeneous treatment effects after a credible identification strategy. Do not use CATE discovery as proof of causality. Separate heterogeneity discovery from validation. Report subgroup stability and calibration.

## Policy Learning

Use when the goal is not just estimating “what happened,” but choosing who should receive a policy. Define welfare objective, budget, fairness constraints, and cost of intervention. Evaluate policy value out-of-sample.

## Modern DID caveat

For staggered policy adoption, avoid naive two-way fixed effects as the only result when treatment effects may be heterogeneous. Ask Codex to check adoption timing and recommend modern DID alternatives or event-study estimators.

## Synthetic DID / Matrix Completion

Useful when panel data exhibit latent factor structure. Requires enough pre-periods and convincing placebo tests. Treat as a complement to classical synthetic control and DID.

## Sensitivity and partial identification

When assumptions are not fully credible, report how large hidden bias would need to be to overturn the conclusion, or report bounds rather than a point estimate.
