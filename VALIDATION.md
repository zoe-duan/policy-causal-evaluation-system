# Validation record

Updated package: native V2 plus top-level study orchestrator, with compatibility and packaging fixes applied.

## Fixes applied in this patched package

- Restored the native V2 top-level Python exports in `src/causal_policy_system/__init__.py`:
  - `MethodRecommendation`
  - `recommend_methods`
  - `load_design_card`
  - `validate_design_card`
- Kept the orchestrator module available in `__all__` as `study_orchestrator`.
- Removed local test/cache artifacts such as `.pytest_cache` and `__pycache__` from the distributable package.
- Consolidated duplicate README orchestrator sections into a single workflow entry and fixed the workflow heading order.
- Made this validation note environment-sensitive: Codex CLI availability depends on the user's local setup and is not bundled with this repository.

## Checks run in the patch sandbox

```bash
python -m py_compile \
  src/causal_policy_system/__init__.py \
  src/causal_policy_system/study_orchestrator.py \
  scripts/continue_study.py \
  scripts/causal_policy_cli.py \
  scripts/validate_setup.py \
  .codex/hooks/user_prompt_context.py

PYTHONPATH=src python - <<'PY'
from causal_policy_system import MethodRecommendation, recommend_methods, load_design_card, validate_design_card
import causal_policy_system
print('legacy_imports_ok', causal_policy_system.__version__)
PY

python scripts/continue_study.py --status
python scripts/continue_study.py --slug sample_policy_doc --next-stage design-review --dry-run
python scripts/causal_policy_cli.py continue-study --slug sample_policy_doc --next-stage data-prep --dry-run
python scripts/validate_setup.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/smoke_test.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q
```

## Results

- Python compile checks passed.
- Legacy top-level imports passed: `from causal_policy_system import MethodRecommendation, recommend_methods, load_design_card, validate_design_card`.
- Study orchestrator status and dry-run commands passed.
- `validate_setup.py` passed. It reported a warning in this environment because Codex CLI was not on `PATH`; install Codex CLI locally before starting an interactive Codex session.
- `smoke_test.py` passed.
- Pytest passed: 11 tests.

## Notes

- Real hosted Codex execution still requires the user's authenticated Codex/ChatGPT session or API-key setup.
- The top-level orchestrator never treats generated demo data as real evidence; demo outputs are marked `DEMO DATA`.
