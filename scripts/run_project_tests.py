#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    import tests.test_design_card as td
    import tests.test_estimators as te
    import tests.test_method_router as tm
    import tests.test_policy_documents as tp

    checks = [
        ("design card validates", td.test_example_design_card_validates),
        ("demo estimators run", te.test_demo_estimators_run),
        ("method router DID", tm.test_panel_policy_routes_to_did),
        ("method router RDD", tm.test_cutoff_routes_to_rdd),
        ("method router heterogeneity", tm.test_heterogeneity_routes_to_forest),
        ("policy document sample parse", tp.test_policy_document_sample_parse),
        ("policy source plan", tp.test_policy_source_plan_mentions_official_sources),
    ]
    for name, func in checks:
        func()
        print(f"PASS: {name}")
    with tempfile.TemporaryDirectory() as d:
        tp.test_policy_document_outputs(Path(d))
        print("PASS: policy document outputs")
    print("All project tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
