# AGENTS.md — Causal Policy Codex System

## Mission

You are working inside a Codex-native causal inference and policy evaluation system. Your job is to help the user turn policy/event hypotheses into credible, reproducible research designs and analysis artifacts.

Default language: Chinese, unless the user asks otherwise. Use precise causal inference terminology in English when it improves clarity: estimand, identification, overlap, parallel trends, CATE, DML, GRF, policy learning.

## Repository map

- `.codex/skills/`: Codex skills. Prefer these over ad hoc prompting.
- `.codex/agents/`: custom subagents for policy-source scouting, policy-document processing, event research, identification, method routing, data design, estimation, robustness, and policy translation.
- `knowledge/`: method memory, policy-source inventory, policy-document processing protocol, and method playbook.
- `templates/`: reusable design cards, reports, checklists.
- `prompts/`: copy-ready prompts for Codex interactive or `codex exec` workflows.
- `src/causal_policy_system/`: lightweight Python helpers.
- `scripts/`: CLI, validation, demos, and the top-level study orchestrator (`continue_study.py`).
- `studies/`: user-created studies. Do not delete.
- `examples/`: demo inputs and outputs.

## Top-level study orchestration

When the user says “继续”, “下一步”, “然后呢”, “推进到数据阶段”, “推进到 first-pass estimation”, or asks to continue an existing study, do **not** ask them to write a long prompt. Use `$advance-study-stage` and the deterministic orchestrator.

Preferred commands:

```bash
python scripts/continue_study.py --slug <slug> --status
python scripts/continue_study.py --slug <slug> --next-stage auto --dry-run
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data
```

The orchestrator runs a design/policy-fact gate before data or estimation. If real data are missing, demo data may be generated only when explicitly permitted, must stay marked as `DEMO DATA`, and must never be interpreted as empirical evidence.

Artifacts created by orchestration include `policy_source_collection_todo.md`, `design_review.md`, `data_sources.md`, `data_readiness_check.md`, `data/processed/analysis_panel.csv`, `tables/event_study_results.csv`, `estimation_report.md`, `study_state.yaml`, `workflow_state.json` / `workflow_state.md`, `orchestrator_summary.md`, and `orchestrator_report.md` when applicable.

## Always follow the causal roadmap

For any policy evaluation or causal question, structure the work as:

1. **Question**: policy/event, target population, time, place, unit of analysis.
2. **Estimand**: ATE, ATT, CATE, dynamic effect, LATE, policy value, spillover effect.
3. **Treatment and outcome**: treatment timing/intensity, outcome definition, measurement window.
4. **Causal graph / mechanism**: confounders, mediators, colliders, selection, spillovers, anticipation.
5. **Identification**: what assumptions make the estimand learnable from the data?
6. **Policy-source plan**: authoritative documents, implementation rules, policy timeline, evidence log, and unresolved factual uncertainty.
7. **Data plan**: units, time, treatment, outcome, covariates, missingness, versioned data source log.
8. **Method recommendation**: primary method, fallback method, why not other methods.
9. **Diagnostics**: pre-trends, overlap, balance, first stage, placebo, donor weights, residual checks.
10. **Robustness**: alternative windows, outcomes, controls, clustering, placebo policies, sensitivity.
11. **Interpretation**: causal vs descriptive, external validity, implementation heterogeneity, ethics.
12. **Reproducibility**: scripts, seeds, session info, data dictionary, report with citations.

Never jump from correlation to causal interpretation. If identification is weak, say so and propose data/design upgrades.


## Policy document and source workflow

Before coding treatment or estimating effects, verify the policy facts:

1. Run `$policy-source-scout` or `python scripts/causal_policy_cli.py policy-source-plan --question "..."`.
2. Prioritize official legal text, gazettes, regulator notices, local implementation rules, statistical/data portals, budget/procurement files, and enforcement records.
3. Store raw policy files under `studies/<slug>/policy_documents/raw/`; do not overwrite them.
4. Run `$policy-document-processor` or `python scripts/causal_policy_cli.py process-policy-doc --input studies/<slug>/policy_documents/raw --study-slug <slug>`.
5. Manually review extracted dates, scope, exemptions, intensity, and enforcement; automated extraction is a first pass.
6. Only then encode `treatment.definition`, `treatment.timing`, and `data_requirements.sources` in the design card.

Always separate announcement/publication/effective/implementation/revision dates. When sources conflict, preserve the conflict and explain how alternative timing choices affect identification.

## Method routing rules

Use `knowledge/method_matrix.md` and `$causal-method-router` first. Initial routing heuristics:

- Random assignment or phased randomized rollout → experiment / encouragement design / cluster RCT analysis.
- Treated and comparison units observed before and after policy → DID / event study; test pre-trends and staggered adoption issues.
- One or few treated aggregate units with many potential donors → synthetic control / synthetic DID / matrix completion.
- Assignment threshold or score cutoff → RDD; inspect manipulation and bandwidth sensitivity.
- Plausible exogenous instrument → IV / 2SLS / LATE; audit relevance, exclusion, monotonicity, weak IV.
- High-dimensional confounders with selection on observables → DML / AIPW / DR learner; require overlap and cross-fitting.
- Heterogeneous effects or targeting → causal forest / GRF / CATE learners / policy learning; separate discovery and validation.
- Severe spillovers/equilibrium effects → warn that standard SUTVA may fail; consider spatial/network/structural designs.
- No credible comparison or data → produce a data acquisition and identification improvement plan instead of over-claiming.



## Codex workflow expectations

For substantial or ambiguous tasks:

1. Enter plan mode or provide a short plan.
2. Read the relevant knowledge files and skill instructions.
3. Create or update a design card in `studies/<slug>/design_card.yaml`.
4. Use subagents explicitly when parallel review is helpful.
5. Run relevant validation or demo scripts before finalizing.
6. In the final answer, include files changed, checks run, causal claims supported, and unresolved risks.

## Subagent usage

When the user asks for a broad evaluation, explicitly ask Codex to spawn focused agents:

- `policy_source_scout`: authoritative policy source reconnaissance.
- `policy_document_processor`: local policy-file extraction and evidence-log updates.
- `event_scout`: public/event/data source reconnaissance.
- `identification_auditor`: causal graph, assumptions, threats.
- `method_router_agent`: method fit and alternatives.
- `data_engineer_agent`: panel/unit/time/data dictionary design.
- `estimator_agent`: code and estimator implementation.
- `robustness_reviewer`: adversarial critique and robustness checklist.
- `policy_translator`: policy memo interpretation and decision relevance.
- `study_orchestrator`: route an existing study through design review, data prep, first-pass estimation, and reporting.

Do not spawn subagents for tiny tasks.

## Quality gates

Before claiming a workflow is done, run what applies:

```bash
python scripts/validate_setup.py
python scripts/smoke_test.py
python scripts/causal_policy_cli.py validate-card <path>
python scripts/run_demo_analysis.py
```

For real studies, prefer:

```bash
python scripts/causal_policy_cli.py recommend --question "..."
python scripts/causal_policy_cli.py validate-card studies/<slug>/design_card.yaml
```

If you edit Python code, run `python scripts/smoke_test.py` at minimum. If dependencies are installed, run `python -m pytest`.

## Data and safety rules

- Never delete `data/raw`, `studies/`, or user-provided files.
- Never fabricate citations, policy dates, law names, sample sizes, data sources, or policy-document contents.
- For current events, laws, public figures, prices, or policy details, use live web search and cite primary/authoritative sources.
- Keep raw data and raw policy documents immutable; write transformed data to `data/processed` or `studies/<slug>/data/processed`, and extracted policy records to `studies/<slug>/policy_documents/processed`.
- Keep secrets out of files and prompts.
- If data may identify people, recommend privacy-preserving aggregation and IRB/ethics review.

## Reporting standard

Every policy evaluation report should have:

- Executive summary with claim strength: `strong`, `moderate`, `weak`, or `design-only`.
- Research question and estimand.
- Data and sample definition.
- Identification assumptions.
- Main results with uncertainty.
- Diagnostics and robustness.
- Threats to validity.
- Policy interpretation.
- Reproducibility appendix.

## Done means

A task is done only when it leaves behind a reusable artifact: a design card, method recommendation, data plan, script, diagnostic checklist, or report. Short chat-only answers are acceptable only for quick conceptual questions.
