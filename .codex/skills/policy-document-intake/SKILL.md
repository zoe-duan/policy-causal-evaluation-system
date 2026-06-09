---
name: policy-document-intake
description: Use when a task needs policy discovery, policy source collection, official document verification, legal/regulatory text parsing, or conversion of policy files into treatment timing and evidence logs.
---

## Goal

Turn policy rumors, news, laws, notices, regulations, budget rules, executive orders, platform rules, and implementation documents into auditable research inputs.

## Workflow

1. Define the policy object: name, jurisdiction, issuing agency, legal form, domain, affected population, and mechanism.
2. Search primary sources first: official legal text, gazettes, regulator notices, local implementation rules, statistical/data portals, budget/procurement/enforcement files, or official platform policy archives.
3. Treat news and commentary as discovery leads only unless no primary source exists; label them clearly.
4. Capture raw source files under `studies/<slug>/policy_documents/raw/` and keep them immutable.
5. Parse local files with:

```bash
python scripts/causal_policy_cli.py process-policy-doc \
  --input studies/<slug>/policy_documents/raw \
  --study-slug <slug>
```

For direct URL capture:

```bash
python scripts/causal_policy_cli.py policy-fetch \
  --url "https://..." \
  --out-dir studies/<slug>/policy_documents/raw \
  --parse
```

6. Extract and verify publication date, effective/implementation date, amendment/repeal date, issuing agency, jurisdiction, covered units, exemptions, thresholds, treatment intensity, and enforcement variation.
7. Translate policy text into treatment variables: binary treatment, event time, dose/intensity, eligibility, exposure, or staggered adoption date.
8. Put unresolved items into the design card as threats or data requirements.

## Output

- Source register with authority scores and hashes.
- Structured policy record JSON/YAML.
- Treatment coding proposal.
- Timeline table.
- Verification gaps and next searches.
