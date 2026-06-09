---
name: causal-dag-identification
description: Use for DAG construction, adjustment set reasoning, identification assumptions, bad controls, mediators, colliders, spillovers, and causal threat audits.
---


## Goal

Audit whether a causal effect is identified, and what assumptions are required.

## Workflow

1. List nodes: treatment, outcome, assignment variables, confounders, mediators, colliders, sample selection, measurement processes.
2. Draft directed edges in text.
3. Mark variables as pre-treatment, post-treatment, or ambiguous.
4. Identify adjustment set candidates and variables not to control for.
5. Check SUTVA/interference, anticipation, timing, measurement changes, selection.
6. Produce falsification and negative-control suggestions.

## Output

- `DAG in words`
- `Adjustment set`
- `Do-not-control variables`
- `Untestable assumptions`
- `Diagnostics / falsification`
- `Identification verdict`: strong / moderate / weak / design-only

## Guardrail

A pretty DAG does not prove identification. Explain why the design generates counterfactual comparison.

