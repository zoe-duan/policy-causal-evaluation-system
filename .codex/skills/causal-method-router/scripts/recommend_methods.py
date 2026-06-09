#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
from causal_policy_system.method_router import main
if __name__ == "__main__":
    main()
