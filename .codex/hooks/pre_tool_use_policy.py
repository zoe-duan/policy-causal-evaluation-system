#!/usr/bin/env python3
"""Codex PreToolUse hook: block destructive shell commands in this repo.

The hook receives a JSON object on stdin. For Bash, the command is usually
available at payload["tool_input"]["command"]. It returns the Codex hook-specific
JSON deny shape when a command violates repository policy.
"""
from __future__ import annotations

import json
import re
import sys

DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\s+(/|\.|~|\*)", "Refusing broad rm -rf deletion."),
    (r"\brm\s+-rf\s+(studies|examples|data|\.codex)\b", "Refusing to delete protected project areas."),
    (r"\bgit\s+reset\s+--hard\b", "Refusing git reset --hard without explicit human review."),
    (r"\bgit\s+clean\s+-[^\n]*[fdx]", "Refusing git clean that may delete untracked work."),
    (r"\bsudo\b", "Refusing sudo from Codex workflow."),
    (r"(curl|wget)\b[^\n|;]*\|\s*(sh|bash|python)", "Refusing pipe-to-shell installer pattern."),
    (r"\bchmod\s+-R\s+777\b", "Refusing chmod -R 777."),
    (r"\b(find\s+.+-delete)\b", "Refusing find -delete; ask user first."),
    (r"\b(export|printenv|env)\b.*(OPENAI|API_KEY|TOKEN|SECRET|PASSWORD)", "Refusing command that may expose secrets."),
]

PROTECTED_WRITES = [
    r">\s*studies/[^\s]+/data/raw/",
    r">\s*data/raw/",
]


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else ""
    if not isinstance(command, str) or not command.strip():
        return 0

    compact = " ".join(command.split())
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, compact, flags=re.IGNORECASE):
            deny(reason)
            return 0
    for pattern in PROTECTED_WRITES:
        if re.search(pattern, compact, flags=re.IGNORECASE):
            deny("Do not overwrite raw data paths. Write to processed/ or outputs/ instead.")
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
