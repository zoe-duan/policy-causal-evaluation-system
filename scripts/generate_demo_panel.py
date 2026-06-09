#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from causal_policy_system.estimators import generate_demo_panel


def main() -> int:
    out = ROOT / "examples" / "data" / "demo_panel.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_demo_panel()
    df.to_csv(out, index=False)
    print(f"Wrote {out} ({len(df)} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
