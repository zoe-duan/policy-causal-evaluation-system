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
from causal_policy_system.method_router import recommend_methods
from causal_policy_system.reporting import render_evaluation_report, write_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--title", default="政策评估初步报告")
    parser.add_argument("--metadata", default="{}", help="JSON metadata")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    metadata = json.loads(args.metadata)
    recs = recommend_methods(args.question, metadata=metadata)
    content = render_evaluation_report(title=args.title, question=args.question, recommendations=recs)
    write_markdown_report(args.output, content)
    print(f"Wrote {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
