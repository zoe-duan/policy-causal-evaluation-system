#!/usr/bin/env python3
"""Codex UserPromptSubmit hook: add causal workflow context for relevant prompts.

This hook never mutates files. It only adds routing context so short prompts like
"继续 ULEZ demo" activate the top-level orchestrator instead of forcing the user
to write a long procedural prompt.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

KEYWORDS = [
    "因果", "政策", "评估", "处理效应", "DID", "双重差分", "合成控制", "工具变量",
    "断点", "RDD", "DML", "因果森林", "CATE", "policy", "causal", "treatment",
    "counterfactual", "effect", "intervention", "event study", "evaluation",
]

ADVANCE_KEYWORDS = [
    "继续", "然后", "下一步", "推进", "进入数据", "估计阶段", "第一版估计", "自动调用",
    "first-pass", "first pass", "estimation", "continue", "advance", "next stage", "next step",
]

CONTEXT = """
For this prompt, use the repository causal roadmap: question → estimand → treatment/outcome → DAG/mechanism → identification → policy-source plan → data plan → method recommendation → diagnostics → robustness → interpretation → reproducibility. If policy/event facts may be current or external, verify them with live web search and cite authoritative sources. Do not make causal claims without explicit identification assumptions.
""".strip()

ADVANCE_CONTEXT_TEMPLATE = """
This prompt appears to be a request to continue or advance an existing study. Use the `$advance-study-stage` skill and the top-level orchestrator instead of asking the user to write a long prompt.

Recommended workflow:
1. Infer the study slug from the prompt or scan `studies/`.
2. Run: `python scripts/continue_study.py --slug <slug> --next-stage auto --dry-run`.
3. If the user asks for first-pass estimation, run: `python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data` when demo data are allowed.
4. Summarize completed actions, skipped actions, warnings, outputs, and whether any outputs are DEMO DATA.

Candidate study slugs detected: {slugs}
""".strip()


def _candidate_slugs() -> str:
    try:
        root = Path(__file__).resolve().parents[2]
        studies = root / "studies"
        slugs = [p.name for p in studies.iterdir() if p.is_dir() and not p.name.startswith(".")]
        return ", ".join(slugs[:8]) if slugs else "none"
    except Exception:
        return "unknown"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str):
        return 0
    contexts: list[str] = []
    if any(re.search(re.escape(k), prompt, flags=re.IGNORECASE) for k in KEYWORDS):
        contexts.append(CONTEXT)
    if any(re.search(re.escape(k), prompt, flags=re.IGNORECASE) for k in ADVANCE_KEYWORDS):
        contexts.append(ADVANCE_CONTEXT_TEMPLATE.format(slugs=_candidate_slugs()))
    if contexts:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(contexts),
            }
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
