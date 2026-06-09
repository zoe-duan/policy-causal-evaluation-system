# Stage router reference

The top-level router maps study artifacts to stages:

1. `empty`: study exists but no design/policy/data artifacts.
2. `policy_facts`: source register or extraction exists, but design is not ready.
3. `design_only`: `design_card.yaml` exists; next step is data preparation.
4. `data_prepared`: `data_sources.md` or `data_readiness_check.md` exists; next step is panel/estimation.
5. `panel_ready`: `data/processed/analysis_panel.csv` exists; next step is first-pass estimation.
6. `first_pass_estimated`: event-study table and estimation report exist; next step is robustness.
7. `robustness_reviewed`: robustness plan/review exists.

The router writes state files in the study folder:

- `study_state.yaml`
- `workflow_state.json`
- `workflow_state.md`
- `logs/orchestrator_run_*.json`
