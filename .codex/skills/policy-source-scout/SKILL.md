---
name: policy-source-scout
description: Use for collecting authoritative policy sources, official documents, implementation rules, data portals, and evidence logs before causal design or estimation.
---

## Goal

Turn a broad policy/event idea into a verified policy-source collection plan and evidence log.

## When to use

- The user mentions a real policy, regulation, law, public program, platform rule, subsidy, tax, ban, pilot, or reform.
- The evaluation depends on exact policy dates, scope, treatment intensity, or implementation details.
- Current or external facts matter.

## Workflow

1. Define the factual questions to verify: policy name, version, issuer, jurisdiction, announcement/publication/effective/implementation dates, treated units, exclusions, enforcement, and concurrent policies.
2. Read `knowledge/policy_source_inventory.md` and `knowledge/policy_document_processing.md`.
3. Search authoritative sources first: law/regulation text, official gazette, regulator/department pages, local implementation rules, statistical/data portals, budget/procurement/enforcement records.
4. Treat media and reports as leads only unless no primary source exists; label them `lead_only`.
5. Create or update `studies/<slug>/policy_documents/source_register.csv` using `templates/policy_source_register.csv`.
6. If source files are available locally, hand off to `$policy-document-processor`.

## Local helper

```bash
python scripts/causal_policy_cli.py policy-source-plan --question "<policy question>"
```

## Output

- Source collection plan.
- Authority-ranked source table.
- Unresolved factual uncertainties.
- Files to fetch or request.
- How each source will affect treatment coding and identification.

## Guardrails

Never invent policy dates, source URLs, law names, sample sizes, or data availability. If a source is not authoritative, say so.
