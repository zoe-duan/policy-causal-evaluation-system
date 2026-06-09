#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
from causal_policy_system.estimators import demo_dml
if __name__ == "__main__":
    demo_dml()
