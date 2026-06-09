---
name: iv-rdd-design
description: Use for instrumental variables, encouragement designs, 2SLS, threshold/cutoff policies, regression discontinuity, weak-IV and manipulation diagnostics.
---


## Goal

Assess IV or RDD designs for policy evaluation.

## IV workflow

1. Define instrument Z, treatment D, outcome Y.
2. Check relevance: does Z shift D?
3. Check exclusion: does Z affect Y only through D?
4. Check independence/as-if random assignment of Z.
5. Check monotonicity if interpreting LATE.
6. Plan first-stage diagnostics and weak-IV robust inference.
7. Report LATE population carefully.

## RDD workflow

1. Define running variable, cutoff, treatment rule, and bandwidth.
2. Verify discontinuity in treatment at cutoff.
3. Check manipulation/sorting around cutoff.
4. Check covariate continuity.
5. Estimate local effect across bandwidths and polynomial orders.
6. Report local nature of estimand.

## Output

- IV/RDD validity table.
- Diagnostics to run.
- “Do not use” verdict if assumptions are not plausible.

