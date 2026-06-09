#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import shutil
import stat
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REQUIRED_FILES = [
    "AGENTS.md",
    "START_HERE.md",
    "README.md",
    ".codex/config.toml",
    ".codex/hooks.json",
    "knowledge/method_playbook.md",
    "knowledge/method_matrix.md",
    "knowledge/causal_roadmap.md",
    "knowledge/policy_discovery_playbook.md",
    "knowledge/policy_document_processing.md",
    "knowledge/policy_source_inventory.md",
    "schemas/design_card.schema.json",
    "scripts/causal_policy_cli.py",
    "scripts/continue_study.py",
    "src/causal_policy_system/method_router.py",
    "src/causal_policy_system/policy_documents.py",
    "src/causal_policy_system/study_orchestrator.py",
]
REQUIRED_SKILLS = [
    "policy-evaluation-intake",
    "policy-source-scout",
    "policy-document-intake",
    "policy-document-processor",
    "causal-method-router",
    "causal-dag-identification",
    "did-event-study",
    "synthetic-control",
    "iv-rdd-design",
    "dml-doubly-robust",
    "causal-forest-policy-learning",
    "robustness-sensitivity",
    "replication-report",
    "event-research-scout",
    "advance-study-stage",
]
REQUIRED_AGENTS = [
    "policy_source_scout.toml",
    "policy_document_processor.toml",
    "event_scout.toml",
    "method_router_agent.toml",
    "identification_auditor.toml",
    "data_engineer_agent.toml",
    "estimator_agent.toml",
    "robustness_reviewer.toml",
    "policy_translator.toml",
    "study_orchestrator.toml",
]
REQUIRED_IMPORTS = ["pandas", "numpy", "scipy", "statsmodels", "sklearn", "yaml", "jsonschema"]


def check_path(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for rel in REQUIRED_FILES:
        check_path(ROOT / rel, errors)
    for skill in REQUIRED_SKILLS:
        check_path(ROOT / ".codex" / "skills" / skill / "SKILL.md", errors)
    for agent in REQUIRED_AGENTS:
        check_path(ROOT / ".codex" / "agents" / agent, errors)

    hooks_path = ROOT / ".codex" / "hooks.json"
    if hooks_path.exists():
        try:
            json.loads(hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"hooks.json is not valid JSON: {exc}")

    for toml_file in [ROOT / ".codex" / "config.toml", *sorted((ROOT / ".codex" / "agents").glob("*.toml"))]:
        try:
            tomllib.loads(toml_file.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"TOML parse failed for {toml_file.relative_to(ROOT)}: {exc}")

    for hook in (ROOT / ".codex" / "hooks").glob("*.py"):
        mode = hook.stat().st_mode
        if not (mode & stat.S_IXUSR):
            warnings.append(f"Hook is not executable: {hook.relative_to(ROOT)}")

    for name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(name)
        except ImportError:
            errors.append(f"Python package not installed: {name}")
    try:
        import causal_policy_system  # noqa: F401
        import causal_policy_system.policy_documents  # noqa: F401
        import causal_policy_system.study_orchestrator  # noqa: F401
    except Exception as exc:  # pragma: no cover
        errors.append(f"Cannot import causal_policy_system: {exc}")

    if shutil.which("codex") is None:
        warnings.append("Codex CLI not found on PATH. Install it before starting an interactive Codex session.")

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")
        print()
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"- {e}")
        return 1
    print("Validation passed: Codex project files, .codex/skills, .codex/agents, schemas, hooks, and Python dependencies look ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
