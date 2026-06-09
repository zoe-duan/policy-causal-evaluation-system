#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.method_router import infer_metadata_from_text, recommend_methods, recommendations_to_markdown
from causal_policy_system.design_card import load_design_card, validate_design_card, summarize_card, card_to_router_metadata
from causal_policy_system.estimators import load_csv, simple_did, twfe_did, partialling_out_dml
from causal_policy_system.reporting import write_json
from causal_policy_system.policy_documents import (
    policy_source_plan,
    process_policy_documents,
    records_to_markdown,
    write_records_json,
    write_source_register_csv,
)
from causal_policy_system.policy_documents import fetch_policy_url, record_from_file, write_record_yaml, append_evidence_log_csv
from causal_policy_system.study_orchestrator import continue_study as orchestrate_continue_study, inspect_study, resolve_study_slug


def cmd_recommend(args: argparse.Namespace) -> int:
    metadata = infer_metadata_from_text(args.question)
    if args.metadata:
        metadata.update(json.loads(args.metadata))
    recs = recommend_methods(args.question, metadata=metadata, top_k=args.top_k)
    if args.format == "json":
        print(json.dumps([r.to_dict() for r in recs], ensure_ascii=False, indent=2))
    else:
        print(recommendations_to_markdown(recs))
    return 0


def cmd_validate_card(args: argparse.Namespace) -> int:
    card = load_design_card(args.card)
    errors = validate_design_card(card)
    print(summarize_card(card))
    if errors:
        print("\nSchema validation failed:")
        for e in errors:
            print(f"- {e}")
        return 1
    print("\nSchema validation passed.")
    if args.recommend:
        q = card.get("question", "")
        recs = recommend_methods(q, metadata=card_to_router_metadata(card), top_k=4)
        print("\n" + recommendations_to_markdown(recs))
    return 0


def cmd_new_study(args: argparse.Namespace) -> int:
    slug = args.slug
    study_dir = ROOT / "studies" / slug
    study_dir.mkdir(parents=True, exist_ok=True)
    card = {
        "question": args.question,
        "status": "draft",
        "policy_event": {"name": args.event or slug, "jurisdiction": "待填写", "date_or_period": "待填写"},
        "unit_of_analysis": "待填写，例如 city-month / individual / firm-year",
        "treatment": {
            "definition": "待填写",
            "timing": "待填写",
            "assignment_mechanism": "待填写",
            "number_of_treated_units": "待填写",
        },
        "outcomes": [{"name": "待填写", "measurement": "待填写"}],
        "estimand": {"target": "ATT/ATE/CATE/LATE/Policy value 待选择", "population": "待填写"},
        "identification_strategy": {
            "primary_method": "待推荐",
            "secondary_methods": [],
            "assumptions": [],
        },
        "data_requirements": {"structure": "待填写", "sources": [], "minimum_fields": []},
        "diagnostics": [],
        "robustness_checks": [],
        "threats_to_validity": [],
        "deliverables": ["design card", "analysis plan", "replication script", "policy memo"],
    }
    (study_dir / "design_card.yaml").write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (study_dir / "notes.md").write_text("# 研究日志\n\n", encoding="utf-8")
    (study_dir / "policy_documents" / "raw").mkdir(parents=True, exist_ok=True)
    (study_dir / "policy_documents" / "processed").mkdir(parents=True, exist_ok=True)
    (study_dir / "policy_documents" / "source_register.csv").write_text((ROOT / "templates" / "policy_source_log.csv").read_text(encoding="utf-8"), encoding="utf-8")
    (study_dir / "evidence_log.md").write_text((ROOT / "templates" / "evidence_log.md").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Created study at {study_dir}")
    print("Next: codex → ask it to read AGENTS.md, validate the design card, and run method routing.")
    return 0




def cmd_policy_fetch(args: argparse.Namespace) -> int:
    meta = fetch_policy_url(args.url, args.out_dir, timeout=args.timeout)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if args.parse:
        record = record_from_file(meta["text_path"], source_url=args.url)
        output = args.output or str(Path(args.out_dir) / f"{record.source_id}.policy_record.yaml")
        write_record_yaml(record, output)
        append_evidence_log_csv(record, args.evidence_log or str(Path(args.out_dir) / "policy_evidence_log.csv"))
        print(f"\nParsed policy record: {output}")
    return 0


def cmd_policy_parse(args: argparse.Namespace) -> int:
    record = record_from_file(args.input, source_url=args.source_url)
    if args.format == "json":
        print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))
    else:
        output = args.output or str(Path(args.input).with_suffix(".policy_record.yaml"))
        write_record_yaml(record, output)
        print(f"Wrote policy record: {output}")
    if args.evidence_log:
        append_evidence_log_csv(record, args.evidence_log)
        print(f"Appended evidence log: {args.evidence_log}")
    if record.extraction_warnings:
        print("\nWarnings:")
        for w in record.extraction_warnings:
            print(f"- {w}")
    return 0


def cmd_policy_source_plan(args: argparse.Namespace) -> int:
    plan = policy_source_plan(args.question)
    if args.format == "json":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print("# Policy source collection plan\n")
        print(f"Question: {plan['question']}\n")
        print("## Likely domains")
        for d in plan["likely_domains"]:
            print(f"- {d}")
        print("\n## Priority sources")
        for s in plan["priority_sources"]:
            print(f"- {s}")
        print("\n## Must extract")
        for s in plan["must_extract"]:
            print(f"- {s}")
        print(f"\nRecommended folder: `{plan['recommended_folder']}`")
        print(f"Next command: `{plan['next_command']}`")
    return 0


def cmd_process_policy_doc(args: argparse.Namespace) -> int:
    records = process_policy_documents(args.input, jurisdiction=args.jurisdiction)
    if args.study_slug:
        base = ROOT / "studies" / args.study_slug / "policy_documents" / "processed"
        base.mkdir(parents=True, exist_ok=True)
        json_path = base / "policy_document_extraction.json"
        md_path = base / "policy_document_summary.md"
        csv_path = ROOT / "studies" / args.study_slug / "policy_documents" / "source_register.csv"
    else:
        base = Path(args.output_dir or ".")
        base.mkdir(parents=True, exist_ok=True)
        json_path = base / "policy_document_extraction.json"
        md_path = base / "policy_document_summary.md"
        csv_path = base / "source_register.csv"
    write_records_json(json_path, records)
    write_source_register_csv(csv_path, records)
    md = records_to_markdown(records)
    md_path.write_text(md, encoding="utf-8")
    if args.format == "json":
        print(json.dumps([r.to_dict() for r in records], ensure_ascii=False, indent=2))
    else:
        print(md)
        print(f"\nWrote JSON: {json_path}")
        print(f"Wrote source register: {csv_path}")
        print(f"Wrote Markdown summary: {md_path}")
    return 0

def cmd_run_estimator(args: argparse.Namespace) -> int:
    df = load_csv(args.csv)
    if args.estimator == "simple-did":
        result = simple_did(df, outcome=args.outcome, treated=args.treated, post=args.post)
    elif args.estimator == "twfe-did":
        result = twfe_did(df, outcome=args.outcome, treatment=args.treatment, unit=args.unit, time=args.time, covariates=args.covariates or [], cluster=args.cluster)
    elif args.estimator == "dml":
        if not args.covariates:
            raise SystemExit("DML requires --covariates.")
        result = partialling_out_dml(df, outcome=args.outcome, treatment=args.treatment, covariates=args.covariates)
    else:
        raise SystemExit(f"Unsupported estimator: {args.estimator}")
    out = result.to_dict()
    if args.output:
        write_json(args.output, out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0



def cmd_continue_study(args: argparse.Namespace) -> int:
    slug = resolve_study_slug(ROOT, args.slug)
    target = "status" if args.status else args.target
    if target == "status":
        state = inspect_study(ROOT, slug)
        if args.format == "json":
            print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Study: studies/{slug}")
            print(f"Current stage: {state.current_stage}")
            print(f"Next recommended stage: {state.next_recommended_stage}")
            if state.warnings:
                print("Warnings:")
                for warning in state.warnings:
                    print(f"- {warning}")
        return 0
    result = orchestrate_continue_study(
        slug=slug,
        target=target,
        question=args.question,
        demo_if_missing_data=args.demo_if_missing_data,
        dry_run=args.dry_run,
        force=args.force,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("dry_run"):
            print("Study orchestrator dry run: no files changed.")
        else:
            print("Study orchestrator complete.")
        print(f"Study: studies/{slug}")
        print(f"Target: {result['target']}")
        print(f"Stage before: {result['before']['current_stage']}")
        print(f"Stage after:  {result['after']['current_stage']}")
        print("Actions:")
        for action in result.get("actions", []):
            print(f"- {action}")
        warnings = []
        for warning in result.get("warnings", []):
            if warning not in warnings:
                warnings.append(warning)
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        print(f"Summary: {result.get('summary_path')}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Causal policy evaluation helper CLI for Codex workflows")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("recommend", help="Recommend causal methods for a policy question")
    p.add_argument("--question", required=True)
    p.add_argument("--metadata", help="JSON metadata such as {'data_structure':'panel'}")
    p.add_argument("--top-k", type=int, default=4)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("validate-card", help="Validate a design card YAML/JSON")
    p.add_argument("card")
    p.add_argument("--recommend", action="store_true")
    p.set_defaults(func=cmd_validate_card)

    p = sub.add_parser("new-study", help="Create a new study folder")
    p.add_argument("--slug", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--event")
    p.set_defaults(func=cmd_new_study)


    p = sub.add_parser("policy-fetch", help="Fetch a policy URL into an immutable source folder")
    p.add_argument("--url", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--parse", action="store_true", help="Parse the fetched text into a policy record")
    p.add_argument("--output", help="YAML output path for parsed record")
    p.add_argument("--evidence-log", help="CSV evidence log path")
    p.set_defaults(func=cmd_policy_fetch)

    p = sub.add_parser("policy-parse", help="Parse a local policy document into a structured policy record")
    p.add_argument("--input", required=True)
    p.add_argument("--source-url")
    p.add_argument("--output")
    p.add_argument("--evidence-log")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")
    p.set_defaults(func=cmd_policy_parse)


    p = sub.add_parser("policy-source-plan", help="Create a policy-source collection plan for a research question")
    p.add_argument("--question", required=True)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.set_defaults(func=cmd_policy_source_plan)

    p = sub.add_parser("process-policy-doc", help="Extract policy timing, scope, and treatment-coding hints from local policy files")
    p.add_argument("--input", nargs="+", required=True, help="One or more files or folders")
    p.add_argument("--study-slug", help="Write outputs under studies/<slug>/policy_documents/")
    p.add_argument("--output-dir", help="Output directory when --study-slug is not used")
    p.add_argument("--jurisdiction", help="Override detected jurisdiction")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.set_defaults(func=cmd_process_policy_doc)


    p = sub.add_parser("continue-study", help="Advance a study using the top-level stage orchestrator")
    p.add_argument("--slug", help="Study slug under studies/<slug>. If omitted, uses the only or most recently modified study.")
    p.add_argument("--target", "--next-stage", dest="target", default="auto", help="auto, policy-facts, design-review, data-prep, panel, first-pass-estimation, robustness-plan")
    p.add_argument("--question", help="Policy/research question, used if the study needs initialization.")
    p.add_argument("--demo-if-missing-data", action="store_true", help="Generate clearly labelled DEMO DATA if no real analysis_panel.csv exists.")
    p.add_argument("--dry-run", action="store_true", help="Inspect route without creating artifacts.")
    p.add_argument("--status", action="store_true", help="Only inspect and print current study stage.")
    p.add_argument("--force", action="store_true", help="Allow draft design-card creation when facts are incomplete.")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_continue_study)

    p = sub.add_parser("run-estimator", help="Run a baseline estimator on CSV data")
    p.add_argument("--csv", required=True)
    p.add_argument("--estimator", choices=["simple-did", "twfe-did", "dml"], required=True)
    p.add_argument("--outcome", required=True)
    p.add_argument("--treated", default="treated_ever")
    p.add_argument("--post", default="post")
    p.add_argument("--treatment", default="treatment")
    p.add_argument("--unit", default="city")
    p.add_argument("--time", default="month")
    p.add_argument("--cluster")
    p.add_argument("--covariates", nargs="*")
    p.add_argument("--output")
    p.set_defaults(func=cmd_run_estimator)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
