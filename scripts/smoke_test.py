#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.method_router import recommend_methods
from causal_policy_system.estimators import generate_demo_panel, simple_did, twfe_did, partialling_out_dml
from causal_policy_system.design_card import load_design_card, validate_design_card


def main() -> int:
    recs = recommend_methods("某城市限行政策是否降低 PM2.5？有城市-月份面板数据、政策前后、多个未限行城市。")
    assert recs and "DID" in recs[0].method, recs[0].method if recs else "no recommendations"

    df = generate_demo_panel(n_cities=12, n_months=24, treated_cities=3, treatment_start=12)
    did = simple_did(df, outcome="pm25", treated="treated_ever", post="post")
    assert did.n_obs == len(df)
    twfe = twfe_did(df, outcome="pm25", treatment="treatment", unit="city", time="month", covariates=["weather_index"], cluster="city")
    assert twfe.standard_error is not None
    dml = partialling_out_dml(df, outcome="pm25", treatment="treatment", covariates=["weather_index", "month"], n_splits=3)
    assert dml.standard_error is not None

    card_path = ROOT / "examples" / "design_cards" / "urban_transport_pollution.yaml"
    if card_path.exists():
        card = load_design_card(card_path)
        errors = validate_design_card(card)
        assert not errors, errors
    print("Smoke test passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
