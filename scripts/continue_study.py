#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.study_orchestrator import continue_study, inspect_study, normalize_target, resolve_study_slug  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Top-level stage router for policy-evaluation studies. It automatically calls the design-review, data-prep, panel, first-pass estimation, and robustness-plan workflow pieces."
    )
    parser.add_argument("--slug", help="Study slug under studies/<slug>. If omitted, the orchestrator uses the only or most recently modified study.")
    parser.add_argument(
        "--target-stage",
        "--target",
        "--next-stage",
        dest="target_stage",
        default="auto",
        help="auto/next, policy-facts, design-review, data-prep, panel, first-pass-estimation, robustness-plan, or status.",
    )
    parser.add_argument("--question", help="Optional research question, used if the study has no design card yet.")
    parser.add_argument(
        "--demo-if-missing-data",
        action="store_true",
        help="If no real analysis_panel.csv exists, generate clearly labelled DEMO DATA for pipeline testing only.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show routing without performing work.")
    parser.add_argument("--status", action="store_true", help="Only inspect and print the current study stage.")
    parser.add_argument("--force", action="store_true", help="Allow creation of a minimal design card when required.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = "status" if args.status else args.target_stage.strip().lower()
    slug = resolve_study_slug(ROOT, args.slug)
    if target == "status":
        state = inspect_study(ROOT, slug)
        payload = state.to_dict()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Study: {state.study_dir}")
            print(f"Current stage: {state.current_stage}")
            print(f"Next recommended stage: {state.next_recommended_stage}")
            if state.warnings:
                print("Warnings:")
                for w in state.warnings:
                    print(f"- {w}")
        return 0

    try:
        # Validate early to give a friendly CLI error.
        normalize_target(target)
        result = continue_study(
            root=ROOT,
            slug=slug,
            target=target,
            question=args.question,
            demo_if_missing_data=args.demo_if_missing_data,
            dry_run=args.dry_run,
            force=args.force,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"Orchestrator failed: {exc}")
        return 1

    if args.json:
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    else:
        before = result.get("before", {})
        after = result.get("after", {})
        if result.get("dry_run"):
            print("Dry run: no files changed by the top-level orchestrator.")
        else:
            print("Study advanced by top-level orchestrator.")
        print(f"Study: studies/{slug}")
        print(f"Target: {result.get('target')}")
        print(f"Stage before: {before.get('current_stage')}")
        print(f"Stage after: {after.get('current_stage')}")
        if after.get("analysis_panel_is_demo"):
            print("Demo data used: true — outputs are pipeline demonstrations only.")
        else:
            print("Demo data used: false")
        print("\nActions:")
        for action in result.get("actions", []):
            print(f"- {action}")
        warnings = result.get("warnings", [])
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
        if result.get("summary_path"):
            print(f"\nSummary: {result['summary_path']}")
        if result.get("study_state"):
            print(f"State: {result['study_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
