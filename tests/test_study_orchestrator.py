from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.study_orchestrator import continue_study, inspect_study


def test_dry_run_does_not_create_study(tmp_path):
    (tmp_path / "studies").mkdir()
    result = continue_study(root=tmp_path, slug="missing-study", target="auto", dry_run=True)
    assert result["dry_run"] is True
    assert result["before"]["current_stage"] == "empty"
    assert not (tmp_path / "studies" / "missing-study").exists()


def test_first_pass_demo_generates_labelled_outputs(tmp_path):
    (tmp_path / "studies").mkdir()
    result = continue_study(
        root=tmp_path,
        slug="london-ulez-outer-london-2023",
        target="first-pass-estimation",
        demo_if_missing_data=True,
    )
    study_dir = tmp_path / "studies" / "london-ulez-outer-london-2023"
    assert result["after"]["current_stage"] == "first_pass_estimated"
    assert (study_dir / "design_review.md").exists()
    assert (study_dir / "data" / "processed" / "analysis_panel.csv").exists()
    assert (study_dir / "tables" / "event_study_results.csv").exists()
    assert (study_dir / "estimation_report.md").exists()
    assert "DEMO DATA" in (study_dir / "estimation_report.md").read_text(encoding="utf-8")


def test_robustness_stage_detected(tmp_path):
    (tmp_path / "studies").mkdir()
    continue_study(root=tmp_path, slug="demo-policy", target="first-pass-estimation", demo_if_missing_data=True)
    continue_study(root=tmp_path, slug="demo-policy", target="robustness-plan")
    state = inspect_study(tmp_path, "demo-policy")
    assert state.current_stage == "robustness_reviewed"
