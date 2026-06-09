---
name: robustness-sensitivity
description: Use for adversarial causal review, robustness checks, placebo tests, negative controls, sensitivity analysis, and reproducibility audits.
---


## Goal

Stress-test a policy evaluation before reporting.

## Workflow

1. Identify the main causal claim.
2. List identifying assumptions and which are testable.
3. Require diagnostics tied to assumptions.
4. Add falsification tests:
   - placebo dates
   - placebo outcomes
   - untreated units as fake treated
   - negative controls
5. Add robustness:
   - alternative windows
   - alternative comparison groups
   - alternative covariate sets
   - clustered SE choices
   - sensitivity to influential units
6. Audit reproducibility: paths, seeds, data dictionary, environment, citations.
7. Return “approved”, “revise”, or “do not claim causality”.

## Output

- Major risks.
- Must-run checks.
- Nice-to-have checks.
- Reporting language revisions.

