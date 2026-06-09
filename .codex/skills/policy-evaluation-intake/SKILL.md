---
name: policy-evaluation-intake
description: Use for turning a broad policy/event hypothesis into a structured causal design card before choosing estimators.
---


## Goal

Convert a vague policy evaluation idea into a design card and a scoped plan. Trigger for questions like “某政策是否造成某结果”, “evaluate a policy”, “what data/method should I use”, or “is this causal?”.

## Workflow

1. Restate the causal question using: population, unit, time, treatment, outcome, counterfactual.
2. Identify the target estimand: ATE, ATT, CATE, LATE, dynamic ATT, or policy value.
3. Draft a minimal DAG in text: treatment, outcome, confounders, mediators, colliders, selection, spillovers.
4. Ask only for missing details that block design. If details are absent but not blocking, mark them as assumptions.
5. Create or update `studies/<slug>/design_card.yaml` using `templates/design_card.yaml`.
6. Recommend which skill should run next:
   - `$policy-source-scout` if policy facts, source authority, or implementation details are unverified
   - `$policy-document-processor` if local policy files exist
   - `$causal-method-router`
   - `$did-event-study`
   - `$synthetic-control`
   - `$iv-rdd-design`
   - `$dml-doubly-robust`
   - `$causal-forest-policy-learning`
   - `$robustness-sensitivity`

## Output format

- `Design summary`
- `Assumptions made`
- `Blocked information`
- `Initial method candidates`
- `Next action`

## Guardrails

Do not infer policy dates or legal details from memory for current events. Use web search and cite sources when facts matter.

