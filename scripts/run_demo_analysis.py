#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.estimators import generate_demo_panel, simple_did, twfe_did, event_study_coefficients
from causal_policy_system.method_router import recommend_methods
from causal_policy_system.reporting import render_evaluation_report, write_markdown_report, write_json


def main() -> int:
    data_path = ROOT / "examples" / "data" / "demo_panel.csv"
    out_dir = ROOT / "examples" / "outputs"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = generate_demo_panel()
    df.to_csv(data_path, index=False)

    question = "某城市交通限行政策是否降低 PM2.5？我们有城市-月份面板数据、政策前后、多个未限行城市。"
    recs = recommend_methods(question, metadata={"data_structure": "panel", "treatment_timing": "before/after", "unit_of_observation": "city-month"})
    did = simple_did(df, outcome="pm25", treated="treated_ever", post="post")
    twfe = twfe_did(df, outcome="pm25", treatment="treatment", unit="city", time="month", covariates=["weather_index"], cluster="city")
    event = event_study_coefficients(df, outcome="pm25", event_time="event_time", unit="city", time="month", treated_ever="treated_ever", window=(-5, 5))
    event.to_csv(out_dir / "demo_event_study.csv", index=False)

    write_json(out_dir / "demo_estimates.json", {"simple_did": did.to_dict(), "twfe": twfe.to_dict()})
    report = render_evaluation_report(
        title="示例：城市交通限行政策对 PM2.5 的影响",
        question=question,
        recommendations=recs,
        estimates=[did, twfe],
        limitations=[
            "这是合成数据，仅用于验证系统可运行。",
            "真实研究需要处理政策选择、污染物监测口径、气象冲击、相邻城市溢出和工业结构变化。",
            "staggered adoption 时不应只依赖 TWFE；需使用分组-时间 ATT 或稳健事件研究。",
        ],
    )
    write_markdown_report(out_dir / "demo_report.md", report)
    print(f"Demo data: {data_path}")
    print(f"Demo report: {out_dir / 'demo_report.md'}")
    print(f"TWFE estimate: {twfe.estimate:.3f} (se={twfe.standard_error:.3f})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
