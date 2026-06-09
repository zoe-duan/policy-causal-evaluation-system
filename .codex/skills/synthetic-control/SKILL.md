---
name: synthetic-control
description: Use for one or few treated aggregate units with a donor pool and pre/post data; includes donor pool audit, pre-fit, placebo tests, and synthetic control reporting.
---


## Goal

Design synthetic control or synthetic DID analysis.

## When to use

- One city/province/country/firm receives a policy shock.
- Many untreated donor units exist.
- Outcomes are aggregate and pre-periods are long enough.
- Donor units are not contaminated.

## Workflow

1. Define treated unit and intervention date.
2. Define donor pool and exclusion rules.
3. Verify pre-period fit and predictor balance.
4. Estimate synthetic weights.
5. Report post-treatment gap and uncertainty using placebo/permutation logic.
6. Run robustness: leave-one-out donors, alternative pre-periods, placebo treated units.
7. Interpret as treated-unit ATT path, not broad ATE.

## Red flags

- Poor pre-treatment fit.
- Donor pool includes partially treated units.
- Treated unit is outside donor support.
- Multiple concurrent shocks.

