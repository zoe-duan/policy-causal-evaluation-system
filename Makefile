.PHONY: setup check smoke demo recommend status continue first-pass clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

check:
	python scripts/validate_setup.py
	python scripts/smoke_test.py
	python -m pytest

smoke:
	python scripts/smoke_test.py

demo:
	python scripts/run_demo_analysis.py

recommend:
	python scripts/causal_policy_cli.py recommend --question "某城市限行政策是否降低 PM2.5？有城市-月份面板数据、政策前后、多个未限行城市。"

continue-status:
	python scripts/continue_study.py --slug $${SLUG:?set SLUG=<study-slug>} --status

continue-first-pass:
	python scripts/continue_study.py --slug $${SLUG:?set SLUG=<study-slug>} --next-stage first-pass-estimation --demo-if-missing-data

status:
	python scripts/continue_study.py --status

continue:
	python scripts/continue_study.py --next-stage auto

first-pass:
	python scripts/continue_study.py --next-stage first-pass-estimation --demo-if-missing-data


continue-study:
	python scripts/continue_study.py --slug $(SLUG) --next-stage auto --dry-run

ulez-first-pass:
	python scripts/continue_study.py --slug london-ulez-outer-london-2023 --next-stage first-pass-estimation --demo-if-missing-data

clean:
	rm -rf examples/outputs/*.tmp .pytest_cache
