# Stage map

| Current artifacts | Detected stage | Next stage |
|---|---|---|
| no study artifacts | `empty` | `policy-facts` |
| policy source/extraction files only | `policy_facts` | `design-review` |
| `design_card.yaml` exists | `design_only` | `data-prep` |
| `data_sources.md` / `data_readiness_check.md` | `data_prepared` | `first-pass-estimation` |
| `data/processed/analysis_panel.csv` exists | `panel_ready` | `first-pass-estimation` |
| `event_study_results.csv` + `estimation_report.md` | `first_pass_estimated` | `robustness-plan` |
| `robustness_plan.md` exists | `robustness_reviewed` | `done` |

The stage router is implemented in `src/causal_policy_system/study_orchestrator.py` and exposed by:

```bash
python scripts/continue_study.py --slug <slug> --status
python scripts/continue_study.py --slug <slug> --next-stage auto
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data
```
