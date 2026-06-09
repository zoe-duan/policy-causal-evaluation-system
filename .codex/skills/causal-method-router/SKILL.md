---
name: causal-method-router
description: Use for recommending causal inference and policy evaluation methods from design/data features, including DID, synthetic control, IV, RDD, DML, GRF, causal forest, and policy learning.
---


## Goal

Choose a credible identification and estimation strategy. This skill is for method recommendation, not final causal claims.

## Required inputs

- Policy/event description.
- Unit and time structure.
- Treatment timing/intensity.
- Comparison group availability.
- Outcome and covariates.
- Whether heterogeneity or targeting matters.

## Workflow

1. Read `knowledge/method_matrix.md`.
2. Extract design features from the question or design card.
3. Rank methods using design fit:
   - Randomized assignment → experiment.
   - Treated/control + pre/post panel → DID/event study.
   - One/few treated aggregate units + donor pool → synthetic control.
   - Cutoff/threshold → RDD.
   - Plausible exogenous instrument → IV.
   - High-dimensional observed confounding → DML/AIPW.
   - Heterogeneity/targeting → causal forest/GRF/policy learning after identification.
4. For each recommended method include assumptions, diagnostics, robustness checks, and failure modes.
5. Explain methods rejected and why.
6. If using local helper, run:

```bash
python scripts/causal_policy_cli.py recommend --question "<question>"
```

## Output format

A ranked table with columns:

- rank
- method
- why it fits
- identifying assumptions
- diagnostics
- robustness checks
- major risks
- implementation path

End with a recommendation: `primary`, `secondary`, `do not use yet`, or `design-only`.

