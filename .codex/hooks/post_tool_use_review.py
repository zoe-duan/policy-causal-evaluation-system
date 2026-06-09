#!/usr/bin/env python3
"""Codex PostToolUse hook: nudge the model when commands fail or touch important areas."""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    response = payload.get("tool_response") or {}

    status = None
    if isinstance(response, dict):
        status = response.get("exit_code", response.get("status"))
    msg = None
    if status not in (None, 0, "0", "success", "completed"):
        msg = "The previous command appears to have failed. Before continuing, inspect the error, explain whether the causal workflow artifact is affected, and rerun the minimal relevant check."
    elif any(token in command for token in ["design_card", "report", "studies/", "examples/outputs"]):
        msg = "After changing design cards or reports, validate schema and make sure causal claims are labeled as identified, descriptive, or design-only."

    if msg:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": msg,
            }
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
