---
name: causal-forest-policy-learning
description: Use for heterogeneous treatment effects, CATE, generalized random forests, causal forests, uplift modeling, and policy learning/targeting after identification is credible.
---


## Goal

Analyze heterogeneous treatment effects and policy targeting.

## When to use

- A credible identification strategy already exists.
- User asks “who benefits most?”, “policy targeting”, “异质性”, or “CATE”.
- Covariates are pre-treatment and rich enough for heterogeneity.

## Workflow

1. Restate the base identification strategy.
2. Define CATE target and candidate moderators before fishing.
3. Split discovery and validation when possible.
4. Estimate causal forest/GRF or DR learner.
5. Check calibration and subgroup stability.
6. Define a policy rule and welfare objective if doing policy learning.
7. Evaluate policy value out-of-sample and discuss fairness/ethics.

## Output

- CATE summary.
- Top moderators with uncertainty.
- Policy rule candidate.
- External validity and fairness caveats.

## Guardrail

Do not use causal forests as a substitute for identification.

