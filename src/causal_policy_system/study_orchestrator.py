from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import csv
import json
import math
import re

import numpy as np
import pandas as pd
import yaml

from causal_policy_system.design_card import load_design_card, validate_design_card


STAGE_ORDER = [
    "empty",
    "policy_facts",
    "design_only",
    "data_prepared",
    "panel_ready",
    "first_pass_estimated",
    "robustness_reviewed",
]

NEXT_STAGE = {
    "empty": "policy-facts",
    "policy_facts": "design-review",
    "design_only": "data-prep",
    "data_prepared": "first-pass-estimation",
    "panel_ready": "first-pass-estimation",
    "first_pass_estimated": "robustness-plan",
    "robustness_reviewed": "done",
}

TARGET_ALIASES = {
    "auto": "auto",
    "next": "auto",
    "policy": "policy-facts",
    "policy-facts": "policy-facts",
    "policy_facts": "policy-facts",
    "facts": "policy-facts",
    "design": "design-review",
    "design-review": "design-review",
    "design_review": "design-review",
    "data": "data-prep",
    "data-prep": "data-prep",
    "data_prep": "data-prep",
    "panel": "panel",
    "panel-build": "panel",
    "panel_build": "panel",
    "estimation": "first-pass-estimation",
    "estimate": "first-pass-estimation",
    "first-pass": "first-pass-estimation",
    "first_pass": "first-pass-estimation",
    "first-pass-estimation": "first-pass-estimation",
    "first_pass_estimation": "first-pass-estimation",
    "robustness": "robustness-plan",
    "robustness-plan": "robustness-plan",
    "robustness_plan": "robustness-plan",
}


@dataclass
class StudyState:
    slug: str
    study_dir: str
    current_stage: str
    next_recommended_stage: str
    has_policy_source_register: bool
    has_policy_extraction: bool
    has_policy_summary: bool
    has_design_card: bool
    design_card_valid: bool
    design_card_errors: list[str]
    has_method_recommendation: bool
    has_analysis_plan: bool
    has_data_sources: bool
    has_data_readiness_check: bool
    has_analysis_panel: bool
    analysis_panel_rows: int
    analysis_panel_is_demo: bool
    has_event_study_results: bool
    has_estimation_report: bool
    has_robustness_plan: bool
    blocking_issues: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_target(target: str | None) -> str:
    if not target:
        return "auto"
    key = target.strip().lower().replace(" ", "-")
    if key not in TARGET_ALIASES:
        raise ValueError(f"Unknown target stage '{target}'. Choose one of: {sorted(set(TARGET_ALIASES.values()))}")
    return TARGET_ALIASES[key]


def study_path(root: Path, slug: str) -> Path:
    return root / "studies" / slug


def list_study_slugs(root: Path) -> list[str]:
    studies = root / "studies"
    if not studies.exists():
        return []
    return sorted([p.name for p in studies.iterdir() if p.is_dir() and not p.name.startswith(".")])


def resolve_study_slug(root: Path, slug: str | None = None) -> str:
    if slug:
        return slug
    studies = root / "studies"
    candidates = [p for p in studies.iterdir() if p.is_dir() and not p.name.startswith(".")] if studies.exists() else []
    if not candidates:
        raise FileNotFoundError("No study folders found under studies/. Create one or pass --slug.")
    if len(candidates) == 1:
        return candidates[0].name
    # Automatic mode chooses the most recently modified study. The orchestrator summary records the chosen slug.
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return newest.name


def safe_read_text(path: Path, max_chars: int = 20_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars]


def safe_load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def safe_load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except Exception:
        return 0


def detect_demo_flag(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        df = pd.read_csv(path, nrows=200)
    except Exception:
        return False
    if "is_demo_data" not in df.columns:
        return False
    vals = df["is_demo_data"].dropna().astype(str).str.lower().unique().tolist()
    return any(v in {"true", "1", "yes"} for v in vals)


def inspect_study(root: Path, slug: str) -> StudyState:
    sdir = study_path(root, slug)
    policy_dir = sdir / "policy_documents"
    design_card_path = sdir / "design_card.yaml"
    panel_path = sdir / "data" / "processed" / "analysis_panel.csv"
    event_results_path = sdir / "tables" / "event_study_results.csv"

    has_policy_source_register = (policy_dir / "source_register.csv").exists()
    has_policy_extraction = (policy_dir / "processed" / "policy_document_extraction.json").exists()
    has_policy_summary = (policy_dir / "processed" / "policy_document_summary.md").exists()
    has_design_card = design_card_path.exists()

    design_card_valid = False
    design_card_errors: list[str] = []
    if has_design_card:
        try:
            card = load_design_card(design_card_path)
            design_card_errors = validate_design_card(card)
            design_card_valid = not design_card_errors
        except Exception as exc:
            design_card_errors = [f"could not load design card: {exc}"]

    has_method_recommendation = (sdir / "method_recommendation.md").exists()
    has_analysis_plan = (sdir / "analysis_plan.md").exists()
    has_data_sources = (sdir / "data_sources.md").exists()
    has_data_readiness_check = (sdir / "data_readiness_check.md").exists()
    has_analysis_panel = panel_path.exists()
    analysis_panel_rows = count_csv_rows(panel_path)
    analysis_panel_is_demo = detect_demo_flag(panel_path)
    has_event_study_results = event_results_path.exists() and count_csv_rows(event_results_path) > 0
    has_estimation_report = (sdir / "estimation_report.md").exists()
    has_robustness_plan = (sdir / "robustness_plan.md").exists() or (sdir / "robustness_review.md").exists()

    blocking: list[str] = []
    warnings: list[str] = []
    if not sdir.exists():
        blocking.append("study directory does not exist yet")
    if has_design_card and not design_card_valid:
        warnings.append("design_card.yaml exists but does not pass schema validation")
    if has_analysis_panel and analysis_panel_is_demo:
        warnings.append("analysis_panel.csv is marked as DEMO DATA")
    if has_event_study_results and analysis_panel_is_demo:
        warnings.append("event-study outputs are based on DEMO DATA")

    if has_robustness_plan:
        stage = "robustness_reviewed"
    elif has_estimation_report and has_event_study_results:
        stage = "first_pass_estimated"
    elif has_analysis_panel and analysis_panel_rows > 0:
        stage = "panel_ready"
    elif has_data_sources or has_data_readiness_check:
        stage = "data_prepared"
    elif has_design_card:
        stage = "design_only"
    elif has_policy_source_register or has_policy_extraction or has_policy_summary:
        stage = "policy_facts"
    else:
        stage = "empty"

    return StudyState(
        slug=slug,
        study_dir=str(sdir),
        current_stage=stage,
        next_recommended_stage=NEXT_STAGE.get(stage, "done"),
        has_policy_source_register=has_policy_source_register,
        has_policy_extraction=has_policy_extraction,
        has_policy_summary=has_policy_summary,
        has_design_card=has_design_card,
        design_card_valid=design_card_valid,
        design_card_errors=design_card_errors,
        has_method_recommendation=has_method_recommendation,
        has_analysis_plan=has_analysis_plan,
        has_data_sources=has_data_sources,
        has_data_readiness_check=has_data_readiness_check,
        has_analysis_panel=has_analysis_panel,
        analysis_panel_rows=analysis_panel_rows,
        analysis_panel_is_demo=analysis_panel_is_demo,
        has_event_study_results=has_event_study_results,
        has_estimation_report=has_estimation_report,
        has_robustness_plan=has_robustness_plan,
        blocking_issues=blocking,
        warnings=warnings,
    )


def ensure_study_dirs(sdir: Path) -> None:
    for rel in [
        "policy_documents/raw",
        "policy_documents/processed",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/demo",
        "figures",
        "tables",
        "logs",
        "reports",
    ]:
        (sdir / rel).mkdir(parents=True, exist_ok=True)


def infer_question_from_study(sdir: Path, fallback_slug: str, explicit_question: str | None = None) -> str:
    if explicit_question:
        return explicit_question.strip()
    card = safe_load_yaml(sdir / "design_card.yaml")
    if isinstance(card, dict) and card.get("question"):
        return str(card["question"])
    report_text = safe_read_text(sdir / "evaluation_report.md", max_chars=5000)
    match = re.search(r"(?:Research question|研究问题|政策问题)[:：]\s*(.+)", report_text)
    if match:
        return match.group(1).strip()
    if "ulez" in fallback_slug.lower():
        return "2023 年 8 月 29 日伦敦 ULEZ 扩展到外伦敦，是否降低外伦敦 NO2 / PM2.5 并提高车辆合规率？"
    return f"Policy evaluation study: {fallback_slug}"


def infer_policy_name(sdir: Path, slug: str) -> str:
    card = safe_load_yaml(sdir / "design_card.yaml")
    if isinstance(card, dict):
        policy_event = card.get("policy_event") or {}
        if isinstance(policy_event, dict) and policy_event.get("name"):
            return str(policy_event["name"])
    extraction = safe_load_json(sdir / "policy_documents" / "processed" / "policy_document_extraction.json")
    if isinstance(extraction, list) and extraction:
        first = extraction[0]
        if isinstance(first, dict) and first.get("policy_name"):
            return str(first["policy_name"])
    if "ulez" in slug.lower():
        return "London-wide Ultra Low Emission Zone expansion"
    return slug.replace("-", " ")


def infer_treatment_date(sdir: Path, slug: str) -> str:
    card = safe_load_yaml(sdir / "design_card.yaml")
    if isinstance(card, dict):
        policy_event = card.get("policy_event") or {}
        treatment = card.get("treatment") or {}
        for source in [policy_event, treatment]:
            if isinstance(source, dict):
                for key in ["event_date", "date_or_period", "implementation_date", "treatment_date"]:
                    val = source.get(key)
                    if val:
                        text = str(val)
                        m = re.search(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}", text)
                        return m.group(0).replace("/", "-") if m else text
    extraction = safe_load_json(sdir / "policy_documents" / "processed" / "policy_document_extraction.json")
    if isinstance(extraction, list):
        blob = json.dumps(extraction, ensure_ascii=False)
        m = re.search(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}", blob)
        if m:
            return m.group(0).replace("/", "-")
    if "ulez" in slug.lower():
        return "2023-08-29"
    return "TBD"


def create_minimal_design_card(sdir: Path, slug: str, question: str | None = None) -> Path:
    path = sdir / "design_card.yaml"
    if path.exists():
        return path
    q = infer_question_from_study(sdir, slug, question)
    is_ulez = "ulez" in slug.lower() or "伦敦" in q or "ULEZ" in q
    if is_ulez:
        card = {
            "question": q,
            "status": "ready_for_data",
            "policy_event": {
                "name": "London-wide Ultra Low Emission Zone expansion",
                "jurisdiction": "Greater London, United Kingdom",
                "event_date": "2023-08-29",
                "implementation_notes": "Draft card created by top-level orchestrator; verify against policy-source register before causal claims.",
                "source_log": ["studies/london-ulez-outer-london-2023/policy_documents/source_register.csv"],
            },
            "unit_of_analysis": "monitoring-station period or borough period",
            "treatment": {
                "definition": "Newly covered outer London monitoring stations or boroughs after ULEZ expansion",
                "timing": "single implementation date",
                "assignment_mechanism": "observational policy boundary and timing",
                "number_of_treated_units": "multiple outer-London units",
            },
            "outcomes": [
                {"name": "NO2", "measurement": "ambient nitrogen dioxide concentration", "expected_direction": "decrease"},
                {"name": "PM2.5", "measurement": "ambient fine particulate concentration", "expected_direction": "decrease"},
                {"name": "vehicle_compliance_rate", "measurement": "vehicle emissions compliance rate", "expected_direction": "increase"},
            ],
            "estimand": {
                "target": "ATT / dynamic ATT",
                "population": "outer-London units newly exposed to the ULEZ expansion",
                "interpretation": "Average post-expansion change for treated units relative to a credible counterfactual.",
            },
            "identification_strategy": {
                "primary_method": "DID/event-study",
                "secondary_methods": ["generalized synthetic control", "synthetic DID", "matrix completion"],
                "assumptions": ["parallel trends after conditioning", "no severe spillovers", "no unmodeled concurrent shocks", "stable monitoring coverage"],
            },
            "data_requirements": {
                "structure": "panel",
                "sources": ["air quality monitoring data", "weather controls", "traffic controls", "TfL compliance data"],
                "minimum_fields": ["unit_id", "date", "outcome_name", "outcome_value", "treated", "post", "event_time"],
            },
            "diagnostics": ["pre-trend / lead coefficients", "missingness and station coverage", "treated/control descriptive trends", "spillover audit"],
            "robustness_checks": ["placebo date", "placebo geography", "alternative donor pool", "weather controls", "seasonality", "spatial spillover exclusion"],
            "threats_to_validity": ["weather shocks", "concurrent transport or environmental policies", "anticipation", "monitoring-station composition", "spatial spillovers"],
            "deliverables": ["design_review.md", "data_sources.md", "analysis_panel.csv", "event-study figures", "estimation_report.md"],
        }
    else:
        card = {
            "question": q,
            "status": "draft",
            "policy_event": {"name": infer_policy_name(sdir, slug), "jurisdiction": "TBD", "event_date": "2000-01-01", "implementation_notes": "Placeholder date for demo/pipeline routing only. Replace with verified policy date before real analysis.", "source_log": []},
            "unit_of_analysis": "TBD panel unit-period",
            "treatment": {"definition": "Demo treated units after placeholder policy date; replace before real analysis", "timing": "2000-01-01", "assignment_mechanism": "observational policy adoption"},
            "outcomes": [{"name": "primary_outcome", "measurement": "TBD", "expected_direction": "TBD"}],
            "estimand": {"target": "ATT", "population": "treated units", "interpretation": "TBD"},
            "identification_strategy": {"primary_method": "DID/event-study if panel data and credible controls exist", "secondary_methods": ["synthetic control", "DML sensitivity"], "assumptions": ["TBD"]},
            "data_requirements": {"structure": "panel", "sources": [], "minimum_fields": ["unit_id", "date", "outcome_name", "outcome_value", "treated", "post", "event_time"]},
            "diagnostics": ["pre-trend / lead coefficients", "missingness", "balance / overlap"],
            "robustness_checks": ["placebo date", "placebo units", "alternative windows"],
            "threats_to_validity": ["confounding", "spillovers", "concurrent shocks", "measurement changes"],
            "deliverables": ["design_review.md", "data_sources.md", "analysis_panel.csv", "estimation_report.md"],
        }
    path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def write_policy_facts_todo(sdir: Path, slug: str, question: str | None = None) -> Path:
    ensure_study_dirs(sdir)
    q = infer_question_from_study(sdir, slug, question)
    path = sdir / "policy_source_collection_todo.md"
    if path.exists():
        return path
    path.write_text(
        f"""# Policy-source collection TODO

Study: `{slug}`

Question: {q}

Status: **policy facts need verification**

Use this file when the study does not yet contain enough policy-source artifacts for the orchestrator to proceed confidently.

## Required source classes

1. Official legal or scheme text.
2. Implementation or variation order.
3. Government / regulator / agency policy page.
4. Consultation or decision memorandum, if relevant.
5. Enforcement rules, fees, exemptions, penalty rules.
6. Official monitoring or evaluation reports, if available.
7. Official data portal pages for outcome and mechanism data.

## Next Codex action

Run the policy-source workflow before causal estimation:

```bash
python scripts/causal_policy_cli.py policy-source-plan --question "{q}"
```

Then place raw policy documents under:

```text
studies/{slug}/policy_documents/raw/
```

and run:

```bash
python scripts/causal_policy_cli.py process-policy-doc --input studies/{slug}/policy_documents/raw --study-slug {slug}
```

## Gate

Do not run first-pass causal estimation until at least a design card and policy fact record exist, unless the user explicitly requests a demo-only dry run.
""",
        encoding="utf-8",
    )
    return path


def run_design_review(root: Path, slug: str, question: str | None = None) -> dict[str, Any]:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    if not (sdir / "design_card.yaml").exists() and question:
        create_minimal_design_card(sdir, slug, question)
    state = inspect_study(root, slug)
    q = infer_question_from_study(sdir, slug, question)
    policy_name = infer_policy_name(sdir, slug)
    treatment_date = infer_treatment_date(sdir, slug)

    blocking: list[str] = []
    nonblocking: list[str] = []
    fixes: list[str] = []

    if not state.has_design_card:
        blocking.append("Missing design_card.yaml. Create or approve a design card before formal estimation.")
        fixes.append("Create studies/<slug>/design_card.yaml with question, treatment, outcomes, estimand, identification strategy, and data requirements.")
    elif not state.design_card_valid:
        nonblocking.append("design_card.yaml exists but schema validation raised issues.")
        fixes.append("Resolve schema warnings or document why the local design-card variant is acceptable.")

    if not state.has_policy_source_register:
        nonblocking.append("No policy_documents/source_register.csv found. Policy facts may not be fully traceable.")
        fixes.append("Run policy-source-scout and record authoritative sources before treating policy facts as verified.")
    if not state.has_policy_extraction:
        nonblocking.append("No policy_document_extraction.json found. Policy dates/scope/exemptions need extraction or manual confirmation.")
        fixes.append("Run policy-document-processor on raw policy documents and manually check treatment timing/scope.")
    if treatment_date == "TBD":
        blocking.append("Treatment date is not explicit.")
        fixes.append("Record publication, effective, implementation, revision, and enforcement dates separately.")

    if state.has_analysis_panel and state.analysis_panel_is_demo:
        nonblocking.append("Existing analysis_panel.csv is demo data; it can test the pipeline but cannot support substantive claims.")
    if not state.has_analysis_panel:
        nonblocking.append("No analysis panel yet. Estimation requires data/processed/analysis_panel.csv or demo-only generation.")

    # Standard identification threats for policy/event studies.
    identification_risks = [
        "Control units may be indirectly affected by spillovers or anticipation.",
        "Weather, traffic, seasonality, and concurrent policies may confound pollution outcomes.",
        "Monitoring-station composition or measurement changes may affect observed outcomes.",
        "Official monitoring reports can be useful context but are not a substitute for an independently specified design.",
    ]

    if blocking:
        recommendation = "failed"
    elif state.has_design_card and (state.has_policy_source_register or state.has_policy_extraction):
        recommendation = "passed_with_cautions"
    else:
        recommendation = "conditional"

    review = {
        "timestamp": utc_now(),
        "slug": slug,
        "question": q,
        "policy_name": policy_name,
        "treatment_date": treatment_date,
        "design_review_status": recommendation,
        "blocking_issues": blocking,
        "non_blocking_issues": nonblocking,
        "recommended_fixes": fixes,
        "identification_risks": identification_risks,
        "minimum_data_requirements": [
            "unit_id and time/date fields",
            "treated/control or donor-pool assignment",
            "post indicator and event_time relative to treatment date",
            "outcome measurements for pre and post periods",
            "data provenance log and missingness summary",
            "weather/seasonality controls where outcomes are pollution, traffic, health, or energy outcomes",
        ],
        "go_no_go": "go_for_demo_or_data_prep" if recommendation != "failed" else "no_go_for_formal_estimation",
    }

    md_lines = [
        "# Design review",
        "",
        f"Study: `{slug}`",
        f"Timestamp: {review['timestamp']}",
        f"Question: {q}",
        f"Policy: {policy_name}",
        f"Treatment date: {treatment_date}",
        f"Design review status: **{recommendation}**",
        f"Go / no-go: **{review['go_no_go']}**",
        "",
        "## Blocking issues",
    ]
    md_lines.extend([f"- {x}" for x in blocking] or ["- None identified by the automated gate."])
    md_lines.append("\n## Non-blocking issues")
    md_lines.extend([f"- {x}" for x in nonblocking] or ["- None."])
    md_lines.append("\n## Recommended fixes")
    md_lines.extend([f"- {x}" for x in fixes] or ["- Continue to data preparation with caution."])
    md_lines.append("\n## Identification risks to audit")
    md_lines.extend([f"- {x}" for x in identification_risks])
    md_lines.append("\n## Minimum data requirements")
    md_lines.extend([f"- {x}" for x in review["minimum_data_requirements"]])
    md_lines.append("\n## Gate rule")
    md_lines.append("Do not interpret first-pass estimates as causal unless policy facts, data provenance, pre-trends, placebo checks, and spillover audits support the design.")
    (sdir / "design_review.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return review


def write_data_plans(root: Path, slug: str, question: str | None = None) -> dict[str, Path]:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    q = infer_question_from_study(sdir, slug, question)
    is_ulez = "ulez" in slug.lower() or "ULEZ" in q or "伦敦" in q
    if is_ulez:
        source_rows = [
            ("Air quality monitoring", "London Air Quality Network / UK-AIR", "manual CSV or API export", "date, station/site id, pollutant, value, unit, coordinates", "main outcome", "required"),
            ("Weather controls", "UK Met Office or comparable weather data", "manual CSV or API export", "date, temperature, rainfall, wind speed, wind direction, humidity", "confounding control", "strongly recommended"),
            ("Traffic controls", "TfL or UK transport statistics", "manual CSV or API export", "date, geography, vehicle count or flow", "mechanism/confounding control", "optional for first pass"),
            ("Vehicle compliance", "TfL compliance data", "manual CSV/page export", "date/month, geography, vehicle class, compliance rate", "mechanism outcome", "optional for first pass"),
            ("Station metadata", "LAQN / UK-AIR metadata", "CSV", "station id, station name, latitude, longitude, borough, station type", "unit mapping", "required"),
            ("Borough/control mapping", "manual research design file", "CSV", "unit_id, geography_name, treated, donor_pool, exclusion_reason", "treatment coding", "required"),
        ]
    else:
        source_rows = [
            ("Outcome panel", "official statistics / administrative data / trusted public dataset", "CSV", "unit id, date/period, outcome value, source metadata", "main outcome", "required"),
            ("Treatment coding", "policy-source register and design card", "CSV/YAML", "unit id, treated, treatment date, intensity", "treatment definition", "required"),
            ("Covariates", "official controls or validated third-party data", "CSV", "unit id, date/period, covariates", "confounding control", "recommended"),
            ("Unit metadata", "official geography or institutional metadata", "CSV", "unit id, name, coordinates/grouping", "panel joins", "required"),
        ]

    data_sources_path = sdir / "data_sources.md"
    lines = [
        "# Data sources plan",
        "",
        f"Study: `{slug}`",
        f"Question: {q}",
        "",
        "This file is generated by the top-level study orchestrator. It is a plan, not proof that the data have been collected.",
        "",
        "| Source class | Owner / publisher | Expected format | Expected variables | Role in identification | First-pass status |",
        "|---|---|---|---|---|---|",
    ]
    for row in source_rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.extend(
        [
            "",
            "## First-pass minimum",
            "",
            "A first-pass estimate needs a panel with at least:",
            "",
            "- `unit_id`",
            "- `date` or `period`",
            "- `outcome_name`",
            "- `outcome_value`",
            "- `treated`",
            "- `post`",
            "- `event_time`",
            "- `treatment_date`",
            "- `is_demo_data`",
            "",
            "When real data are unavailable, the orchestrator may create demo data only if explicitly allowed. Demo data must remain labelled and cannot support substantive claims.",
        ]
    )
    data_sources_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    readiness_path = sdir / "data_readiness_check.md"
    panel_path = sdir / "data" / "processed" / "analysis_panel.csv"
    panel_status = "available" if panel_path.exists() else "waiting-for-data"
    readiness_lines = [
        "# Data readiness check",
        "",
        f"Study: `{slug}`",
        f"Timestamp: {utc_now()}",
        f"Current panel status: **{panel_status}**",
        "",
        "## Required files",
        "",
        "- `studies/<slug>/design_card.yaml`",
        "- `studies/<slug>/policy_documents/source_register.csv` or documented policy-source TODO",
        "- `studies/<slug>/data/processed/analysis_panel.csv` for estimation",
        "- `studies/<slug>/logs/data_provenance.csv` for real data ingestion, if real data are used",
        "",
        "## Expected schema for `analysis_panel.csv`",
        "",
        "| Column | Required | Notes |",
        "|---|---:|---|",
        "| unit_id | yes | Panel unit. |",
        "| date | yes | ISO date if available. |",
        "| period | yes | Daily/monthly/period identifier. |",
        "| outcome_name | yes | e.g., NO2, PM2.5. |",
        "| outcome_value | yes | Numeric outcome. |",
        "| treated | yes | 1 for treated units, 0 for control/donor units. |",
        "| post | yes | 1 after treatment date for treated timing. |",
        "| event_time | yes | Periods relative to treatment date. Reference period normally -1. |",
        "| treatment_date | yes | Recorded policy implementation date. |",
        "| geography_name | recommended | Human-readable unit/geography. |",
        "| data_source | recommended | Dataset name or provenance pointer. |",
        "| is_demo_data | yes | Must be true for synthetic/demo panels. |",
        "",
        "## Validation checks",
        "",
        "- All required fields are present.",
        "- Outcome values are numeric and not all missing.",
        "- There are treated and control units.",
        "- There is at least one pre-treatment and one post-treatment period.",
        "- Demo data are clearly marked and excluded from substantive conclusions.",
    ]
    readiness_path.write_text("\n".join(readiness_lines) + "\n", encoding="utf-8")
    return {"data_sources": data_sources_path, "data_readiness": readiness_path}


def make_demo_panel(slug: str, treatment_date: str = "2023-08-29", seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    is_ulez = "ulez" in slug.lower()
    if is_ulez:
        treated_units = ["outer_london_station_01", "outer_london_station_02", "outer_london_station_03", "outer_london_station_04"]
        control_units = ["donor_station_01", "donor_station_02", "donor_station_03", "donor_station_04", "donor_station_05", "donor_station_06"]
        outcomes = [("NO2", 32.0, -3.0), ("PM2.5", 11.5, -0.7)]
    else:
        treated_units = [f"treated_unit_{i:02d}" for i in range(1, 5)]
        control_units = [f"control_unit_{i:02d}" for i in range(1, 7)]
        outcomes = [("primary_outcome", 50.0, -2.0)]
    periods = pd.period_range("2022-07", "2024-12", freq="M")
    treatment_period = pd.Period("2023-08", freq="M")
    rows: list[dict[str, Any]] = []
    unit_ids = treated_units + control_units
    unit_effects = {u: rng.normal(0, 2.0) for u in unit_ids}
    for unit in unit_ids:
        treated = int(unit in treated_units)
        for period in periods:
            event_time = int((period.year - treatment_period.year) * 12 + (period.month - treatment_period.month))
            post = int(event_time >= 0)
            date = period.to_timestamp(how="end").strftime("%Y-%m-%d")
            seasonal = math.sin(period.month / 12 * 2 * math.pi)
            weather_index = rng.normal(0, 1)
            traffic_flow = 1000 + 30 * seasonal + rng.normal(0, 60) - 25 * treated * post
            for outcome_name, baseline, effect in outcomes:
                # The demo effect is included only so the estimation pipeline has non-empty results.
                # It is intentionally marked as demo and must not be interpreted substantively.
                slope = -0.03 * event_time
                y = baseline + unit_effects[unit] + 0.9 * seasonal + slope + 0.5 * weather_index + effect * treated * post + rng.normal(0, 1.2)
                rows.append(
                    {
                        "unit_id": unit,
                        "date": date,
                        "period": str(period),
                        "outcome_name": outcome_name,
                        "outcome_value": round(float(y), 4),
                        "treated": treated,
                        "post": post,
                        "event_time": event_time,
                        "treatment_date": treatment_date,
                        "geography_name": unit.replace("_", " "),
                        "data_source": "DEMO DATA generated by scripts/continue_study.py",
                        "is_demo_data": True,
                        "temperature": round(12 + 8 * seasonal + rng.normal(0, 2), 3),
                        "rainfall": max(0.0, round(rng.gamma(1.2, 1.5), 3)),
                        "wind_speed": max(0.1, round(rng.normal(4.0, 1.0), 3)),
                        "traffic_flow": round(float(traffic_flow), 3),
                    }
                )
    return pd.DataFrame(rows)


def validate_panel(df: pd.DataFrame) -> list[str]:
    required = ["unit_id", "period", "outcome_name", "outcome_value", "treated", "post", "event_time", "is_demo_data"]
    errors = [f"missing required column: {c}" for c in required if c not in df.columns]
    if errors:
        return errors
    if df.empty:
        errors.append("analysis panel is empty")
        return errors
    for col in ["outcome_value", "treated", "post", "event_time"]:
        try:
            pd.to_numeric(df[col])
        except Exception:
            errors.append(f"column is not numeric: {col}")
    if df["treated"].nunique(dropna=True) < 2:
        errors.append("panel must contain both treated and control units")
    if df["post"].nunique(dropna=True) < 2:
        errors.append("panel must contain both pre and post periods")
    if df["outcome_name"].nunique(dropna=True) < 1:
        errors.append("panel must contain at least one outcome")
    return errors


def ensure_analysis_panel(root: Path, slug: str, *, demo_if_missing: bool, question: str | None = None) -> tuple[Path, bool, list[str]]:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    panel_path = sdir / "data" / "processed" / "analysis_panel.csv"
    warnings: list[str] = []
    if panel_path.exists():
        df = pd.read_csv(panel_path)
        errors = validate_panel(df)
        if errors:
            raise ValueError("Existing analysis_panel.csv failed validation: " + "; ".join(errors))
        return panel_path, detect_demo_flag(panel_path), warnings
    if not demo_if_missing:
        raise FileNotFoundError(
            "No analysis_panel.csv found. Provide real data under studies/<slug>/data/processed/analysis_panel.csv "
            "or rerun with --demo-if-missing-data for a clearly labelled pipeline demo."
        )
    treatment_date = infer_treatment_date(sdir, slug)
    if treatment_date == "TBD":
        treatment_date = "2023-08-29" if "ulez" in slug.lower() else "2000-01-01"
    df = make_demo_panel(slug, treatment_date=treatment_date)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(panel_path, index=False)
    demo_dir = sdir / "data" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(demo_dir / "analysis_panel_DEMO_DATA.csv", index=False)
    warnings.append("Generated DEMO DATA analysis panel because real data were missing and --demo-if-missing-data was set.")
    report = [
        "# Panel build report",
        "",
        f"Timestamp: {utc_now()}",
        "Status: **DEMO DATA generated**",
        "",
        "This panel is synthetic and exists only to test orchestration, estimation scripts, figures, and reporting. It cannot support policy conclusions.",
        "",
        f"Rows: {len(df)}",
        f"Units: {df['unit_id'].nunique()}",
        f"Periods: {df['period'].nunique()}",
        f"Outcomes: {', '.join(sorted(df['outcome_name'].unique()))}",
        f"Treated units: {df.loc[df['treated'] == 1, 'unit_id'].nunique()}",
        f"Control units: {df.loc[df['treated'] == 0, 'unit_id'].nunique()}",
    ]
    (sdir / "logs" / "panel_build_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return panel_path, True, warnings


def _fit_event_study_for_outcome(df: pd.DataFrame, outcome_name: str, window: tuple[int, int] = (-12, 12), reference: int = -1) -> pd.DataFrame:
    import statsmodels.formula.api as smf

    sub = df[df["outcome_name"].astype(str).str.lower() == outcome_name.lower()].copy()
    if sub.empty:
        return pd.DataFrame()
    for col in ["outcome_value", "treated", "event_time"]:
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
    sub = sub.dropna(subset=["outcome_value", "treated", "event_time", "unit_id", "period"])
    low, high = window
    sub = sub[(sub["event_time"] >= low) & (sub["event_time"] <= high)].copy()
    if sub["unit_id"].nunique() < 3 or sub["period"].nunique() < 4:
        return pd.DataFrame()
    event_values = sorted(int(x) for x in sub["event_time"].dropna().unique() if low <= int(x) <= high)
    event_values = [x for x in event_values if x != reference]
    terms: list[str] = []
    mapping: list[tuple[int, str]] = []
    for k in event_values:
        prefix = "m" if k < 0 else "p"
        col = f"event_{prefix}{abs(k)}"
        sub[col] = ((sub["event_time"] == k) & (sub["treated"].astype(int) == 1)).astype(int)
        if sub[col].sum() > 0:
            terms.append(col)
            mapping.append((k, col))
    if not terms:
        return pd.DataFrame()
    formula = f"outcome_value ~ {' + '.join(terms)} + C(unit_id) + C(period)"
    model = smf.ols(formula, data=sub)
    try:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": sub["unit_id"]})
        covariance = "clustered_by_unit"
    except Exception:
        fit = model.fit(cov_type="HC1")
        covariance = "HC1_fallback"
    rows = []
    for k, col in mapping:
        rows.append(
            {
                "outcome_name": outcome_name,
                "event_time": k,
                "estimate": float(fit.params.get(col, np.nan)),
                "standard_error": float(fit.bse.get(col, np.nan)),
                "reference_period": reference,
                "n_obs": int(fit.nobs),
                "n_units": int(sub["unit_id"].nunique()),
                "n_periods": int(sub["period"].nunique()),
                "covariance": covariance,
                "model": "event-study with unit and period fixed effects",
            }
        )
    return pd.DataFrame(rows)


def _write_trend_plot(sub: pd.DataFrame, outcome_name: str, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    trend = sub.groupby(["period", "treated"], as_index=False)["outcome_value"].mean()
    periods = sorted(trend["period"].astype(str).unique())
    x_map = {p: i for i, p in enumerate(periods)}
    fig, ax = plt.subplots(figsize=(9, 5))
    for treated_value, label in [(0, "control/donor"), (1, "treated")]:
        g = trend[trend["treated"] == treated_value].copy()
        if g.empty:
            continue
        ax.plot([x_map[str(p)] for p in g["period"]], g["outcome_value"], marker="o", linewidth=1.4, label=label)
    ref_rows = sub.loc[sub["event_time"] == 0, "period"].astype(str).unique().tolist()
    if ref_rows:
        ax.axvline(x_map.get(ref_rows[0], 0), linestyle="--", linewidth=1)
    ax.set_title(f"Trend: {outcome_name}")
    ax.set_xlabel("period")
    ax.set_ylabel("outcome value")
    if len(periods) > 12:
        step = max(1, len(periods) // 8)
        ax.set_xticks(list(range(0, len(periods), step)))
        ax.set_xticklabels([periods[i] for i in range(0, len(periods), step)], rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _write_event_plot(results: pd.DataFrame, outcome_name: str, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    sub = results[results["outcome_name"].astype(str).str.lower() == outcome_name.lower()].copy()
    if sub.empty:
        return
    sub = sub.sort_values("event_time")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(sub["event_time"], sub["estimate"], yerr=1.96 * sub["standard_error"], marker="o", linestyle="-")
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.axvline(0, linestyle=":", linewidth=1)
    ax.set_title(f"Event-study coefficients: {outcome_name}")
    ax.set_xlabel("event time")
    ax.set_ylabel("coefficient")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def run_first_pass_estimation(root: Path, slug: str, *, demo_if_missing: bool, question: str | None = None) -> dict[str, Any]:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    panel_path, is_demo, panel_warnings = ensure_analysis_panel(root, slug, demo_if_missing=demo_if_missing, question=question)
    df = pd.read_csv(panel_path)
    errors = validate_panel(df)
    if errors:
        raise ValueError("analysis_panel.csv failed validation: " + "; ".join(errors))

    for col in ["outcome_value", "treated", "post", "event_time"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    summary = df.groupby(["outcome_name", "treated", "post"], as_index=False).agg(
        n_obs=("outcome_value", "count"),
        mean_outcome=("outcome_value", "mean"),
        sd_outcome=("outcome_value", "std"),
        n_units=("unit_id", "nunique"),
    )
    desc_path = sdir / "tables" / "descriptive_summary.csv"
    desc_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(desc_path, index=False)

    outcomes = sorted(str(x) for x in df["outcome_name"].dropna().unique())
    result_frames: list[pd.DataFrame] = []
    for outcome in outcomes:
        sub = df[df["outcome_name"].astype(str) == outcome].copy()
        safe_name = outcome.lower().replace(".", "").replace(" ", "_").replace("/", "_")
        _write_trend_plot(sub, outcome, sdir / "figures" / f"trends_{safe_name}.png")
        es = _fit_event_study_for_outcome(df, outcome, window=(-8, 8), reference=-1)
        if not es.empty:
            result_frames.append(es)
    if result_frames:
        results = pd.concat(result_frames, ignore_index=True)
    else:
        results = pd.DataFrame(columns=["outcome_name", "event_time", "estimate", "standard_error", "reference_period", "n_obs", "n_units", "n_periods", "covariance", "model"])
    results_path = sdir / "tables" / "event_study_results.csv"
    results.to_csv(results_path, index=False)
    for outcome in outcomes:
        safe_name = outcome.lower().replace(".", "").replace(" ", "_").replace("/", "_")
        _write_event_plot(results, outcome, sdir / "figures" / f"event_study_{safe_name}.png")

    demo_flag = bool(is_demo or df.get("is_demo_data", pd.Series([False])).astype(str).str.lower().isin(["true", "1", "yes"]).any())
    report_lines = [
        "# First-pass estimation report",
        "",
        f"Study: `{slug}`",
        f"Timestamp: {utc_now()}",
        f"Data status: **{'DEMO DATA' if demo_flag else 'real/provided panel'}**",
        "Claim strength: **preliminary / not a final causal claim**",
        "",
    ]
    if demo_flag:
        report_lines.extend(
            [
                "## DEMO DATA WARNING",
                "",
                "The analysis panel is marked as demo/synthetic data. The estimates below only demonstrate the pipeline. They do not describe the real policy and must not be cited as substantive evidence.",
                "",
            ]
        )
    report_lines.extend(
        [
            "## Input panel",
            "",
            f"- Path: `{panel_path.relative_to(root)}`",
            f"- Rows: {len(df)}",
            f"- Units: {df['unit_id'].nunique()}",
            f"- Periods: {df['period'].nunique()}",
            f"- Outcomes: {', '.join(outcomes)}",
            f"- Treated units: {df.loc[df['treated'] == 1, 'unit_id'].nunique()}",
            f"- Control/donor units: {df.loc[df['treated'] == 0, 'unit_id'].nunique()}",
            "",
            "## Model specification",
            "",
            "For each outcome, the first-pass event-study regresses `outcome_value` on treated-unit event-time indicators plus unit and period fixed effects. The reference period is `event_time = -1`. Standard errors are clustered by unit when possible, with HC1 fallback if clustered covariance fails.",
            "",
            "## Outputs",
            "",
            f"- Descriptive summary: `{desc_path.relative_to(root)}`",
            f"- Event-study table: `{results_path.relative_to(root)}`",
            "- Figures: `studies/<slug>/figures/`",
            "",
            "## Event-study availability",
        ]
    )
    if results.empty:
        report_lines.append("- No event-study coefficients were estimated because the panel did not have enough usable observations after validation.")
    else:
        for outcome in sorted(results["outcome_name"].unique()):
            sub = results[results["outcome_name"] == outcome]
            lead_rows = sub[sub["event_time"] < 0]
            if not lead_rows.empty:
                max_abs_lead = lead_rows["estimate"].abs().max()
                lead_note = f"max absolute pre-treatment coefficient in window: {max_abs_lead:.3f}"
            else:
                lead_note = "no pre-treatment leads estimated"
            report_lines.append(f"- {outcome}: {len(sub)} event-time coefficients; {lead_note}.")
    report_lines.extend(
        [
            "",
            "## Pre-trend warning",
            "",
            "This automated report does not certify parallel trends. Inspect lead coefficients, treated/control trend figures, station coverage, and placebo checks before interpreting post-treatment coefficients causally.",
            "",
            "## Required next robustness checks",
            "",
            "- Placebo treatment dates.",
            "- Placebo geographies / donor units.",
            "- Weather, seasonality, and traffic controls.",
            "- Alternative control pools and exclusion of nearby spillover-risk units.",
            "- Missingness and monitoring-station composition checks.",
            "- Mechanism analysis if compliance or intermediate outcomes are available.",
            "",
            "## Limitations",
            "",
            "- First-pass estimates are only a starting point.",
            "- Policy facts, data provenance, and control-pool validity must be manually audited.",
            "- Official monitoring reports are context, not independent identification.",
        ]
    )
    (sdir / "estimation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "panel_path": str(panel_path),
        "is_demo_data": demo_flag,
        "descriptive_summary": str(desc_path),
        "event_study_results": str(results_path),
        "outcomes": outcomes,
        "n_rows": int(len(df)),
        "n_event_rows": int(len(results)),
        "warnings": panel_warnings + (["Outputs are based on DEMO DATA."] if demo_flag else []),
    }


def write_robustness_plan(root: Path, slug: str) -> Path:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    path = sdir / "robustness_plan.md"
    if path.exists():
        return path
    lines = [
        "# Robustness and sensitivity plan",
        "",
        f"Study: `{slug}`",
        f"Timestamp: {utc_now()}",
        "",
        "## Required before any strong causal claim",
        "",
        "1. Pre-trend / lead coefficient audit with plotted confidence intervals.",
        "2. Placebo policy dates before actual implementation.",
        "3. Placebo treated units or geographies.",
        "4. Alternative control pools and donor-pool restrictions.",
        "5. Weather, seasonality, and traffic controls where relevant.",
        "6. Spatial spillover exclusion rules.",
        "7. Outcome measurement and station/composition stability checks.",
        "8. Multiple-outcome and multiple-window transparency.",
        "9. Sensitivity to time aggregation and bandwidth/window choices.",
        "10. Mechanism checks using intermediate outcomes if available.",
        "",
        "## Interpretation rule",
        "",
        "Report estimates as preliminary until the above checks are implemented and summarized.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_study_state(root: Path, slug: str, state: StudyState, actions: list[str], target: str, dry_run: bool) -> Path:
    sdir = study_path(root, slug)
    ensure_study_dirs(sdir)
    data = {
        "timestamp": utc_now(),
        "slug": slug,
        "target": target,
        "dry_run": dry_run,
        "actions": actions,
        "state": state.to_dict(),
    }
    path = sdir / "study_state.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    # JSON/Markdown aliases for dashboards, scripts, and users who prefer obvious workflow-state files.
    (sdir / "workflow_state.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md_lines = [
        "# Workflow state",
        "",
        f"- slug: `{slug}`",
        f"- target: `{target}`",
        f"- dry_run: `{dry_run}`",
        f"- current_stage: `{state.current_stage}`",
        f"- next_recommended_stage: `{state.next_recommended_stage}`",
        f"- has_design_card: `{state.has_design_card}`",
        f"- design_card_valid: `{state.design_card_valid}`",
        f"- has_policy_source_register: `{state.has_policy_source_register}`",
        f"- has_policy_extraction: `{state.has_policy_extraction}`",
        f"- has_analysis_panel: `{state.has_analysis_panel}`",
        f"- analysis_panel_is_demo: `{state.analysis_panel_is_demo}`",
        f"- has_estimation_report: `{state.has_estimation_report}`",
        "",
        "## Actions",
        "",
    ]
    md_lines.extend([f"- {a}" for a in actions] or ["- None."])
    if state.warnings:
        md_lines.extend(["", "## Warnings", ""])
        md_lines.extend([f"- {w}" for w in state.warnings])
    (sdir / "workflow_state.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    log_dir = sdir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (log_dir / f"orchestrator_run_{stamp}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_orchestrator_summary(root: Path, slug: str, *, target: str, before: StudyState, after: StudyState, actions: list[str], warnings: list[str]) -> Path:
    sdir = study_path(root, slug)
    lines = [
        "# Orchestrator summary",
        "",
        f"Study: `{slug}`",
        f"Timestamp: {utc_now()}",
        f"Target: `{target}`",
        f"Stage before: `{before.current_stage}`",
        f"Stage after: `{after.current_stage}`",
        "",
        "## Actions taken",
    ]
    lines.extend([f"- {a}" for a in actions] or ["- No actions; dry run or no-op."])
    lines.append("\n## Warnings")
    lines.extend([f"- {w}" for w in warnings] or ["- None."])
    lines.extend(
        [
            "",
            "## Next recommended stage",
            "",
            f"`{after.next_recommended_stage}`",
        ]
    )
    content = "\n".join(lines) + "\n"
    path = sdir / "orchestrator_summary.md"
    path.write_text(content, encoding="utf-8")
    # Backward-compatible, more obvious report name for users.
    (sdir / "orchestrator_report.md").write_text(content, encoding="utf-8")
    return path


def continue_study(
    *,
    root: Path | None = None,
    slug: str | None = None,
    target: str = "auto",
    question: str | None = None,
    demo_if_missing_data: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    root = root or project_root()
    slug = resolve_study_slug(root, slug)
    target = normalize_target(target)
    sdir = study_path(root, slug)
    if not dry_run:
        ensure_study_dirs(sdir)
    before = inspect_study(root, slug)
    if target == "auto":
        target = before.next_recommended_stage
        if target == "done":
            target = "robustness-plan"

    actions: list[str] = []
    warnings: list[str] = list(before.warnings)

    if dry_run:
        after = before
        return {
            "before": before.to_dict(),
            "after": after.to_dict(),
            "target": target,
            "dry_run": True,
            "actions": actions,
            "summary_path": None,
            "study_state": None,
            "warnings": warnings,
        }

    if target in {"policy-facts", "design-review", "data-prep", "panel", "first-pass-estimation", "robustness-plan"}:
        # Always make sure there is at least a place for policy facts.
        if not before.has_policy_source_register and not before.has_policy_extraction:
            todo = write_policy_facts_todo(sdir, slug, question)
            actions.append(f"created/confirmed policy-source TODO: {todo.relative_to(root)}")

    if target == "policy-facts":
        pass

    elif target == "design-review":
        if not (sdir / "design_card.yaml").exists() and (question or force or demo_if_missing_data):
            card_path = create_minimal_design_card(sdir, slug, question)
            actions.append(f"created minimal design card: {card_path.relative_to(root)}")
        review = run_design_review(root, slug, question)
        actions.append(f"wrote design review: {Path(study_path(root, slug) / 'design_review.md').relative_to(root)} ({review['design_review_status']})")

    elif target == "data-prep":
        if not (sdir / "design_card.yaml").exists() and (question or force):
            card_path = create_minimal_design_card(sdir, slug, question)
            actions.append(f"created minimal design card: {card_path.relative_to(root)}")
        review = run_design_review(root, slug, question)
        actions.append(f"wrote design review: {Path(study_path(root, slug) / 'design_review.md').relative_to(root)} ({review['design_review_status']})")
        paths = write_data_plans(root, slug, question)
        actions.append(f"wrote data source plan: {paths['data_sources'].relative_to(root)}")
        actions.append(f"wrote data readiness check: {paths['data_readiness'].relative_to(root)}")

    elif target == "panel":
        review = run_design_review(root, slug, question)
        actions.append(f"wrote design review: {Path(study_path(root, slug) / 'design_review.md').relative_to(root)} ({review['design_review_status']})")
        paths = write_data_plans(root, slug, question)
        actions.append(f"wrote data source plan: {paths['data_sources'].relative_to(root)}")
        panel_path, is_demo, panel_warnings = ensure_analysis_panel(root, slug, demo_if_missing=demo_if_missing_data, question=question)
        actions.append(f"created/validated analysis panel: {panel_path.relative_to(root)}")
        warnings.extend(panel_warnings)
        if is_demo:
            warnings.append("analysis panel is DEMO DATA")

    elif target == "first-pass-estimation":
        if not (sdir / "design_card.yaml").exists() and (question or force or demo_if_missing_data):
            card_path = create_minimal_design_card(sdir, slug, question)
            actions.append(f"created minimal design card: {card_path.relative_to(root)}")
        review = run_design_review(root, slug, question)
        actions.append(f"wrote design review: {Path(study_path(root, slug) / 'design_review.md').relative_to(root)} ({review['design_review_status']})")
        if review["design_review_status"] == "failed" and not force:
            raise RuntimeError("Design review failed. Stop before estimation; fix blocking design/policy issues first. Use --force only for explicit pipeline debugging, not for a research demo.")
        paths = write_data_plans(root, slug, question)
        actions.append(f"wrote data source plan: {paths['data_sources'].relative_to(root)}")
        actions.append(f"wrote data readiness check: {paths['data_readiness'].relative_to(root)}")
        result = run_first_pass_estimation(root, slug, demo_if_missing=demo_if_missing_data, question=question)
        actions.append(f"ran first-pass estimation; report: {Path(study_path(root, slug) / 'estimation_report.md').relative_to(root)}")
        warnings.extend(result.get("warnings", []))

    elif target == "robustness-plan":
        path = write_robustness_plan(root, slug)
        actions.append(f"wrote robustness plan: {path.relative_to(root)}")

    else:
        raise ValueError(f"Unsupported target stage: {target}")

    after = inspect_study(root, slug)
    state_path = write_study_state(root, slug, after, actions, target, dry_run=False)
    summary_path = write_orchestrator_summary(root, slug, target=target, before=before, after=after, actions=actions, warnings=warnings)
    return {
        "before": before.to_dict(),
        "after": after.to_dict(),
        "target": target,
        "actions": actions,
        "warnings": warnings,
        "study_state": str(state_path),
        "summary_path": str(summary_path),
    }
