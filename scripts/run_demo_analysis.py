#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_policy_system.estimators import generate_demo_panel, simple_did, twfe_did, event_study_coefficients
from causal_policy_system.method_router import recommend_methods
from causal_policy_system.reporting import write_markdown_report, write_json


def configure_plots() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "PingFang SC",
                "Heiti SC",
                "Songti SC",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "figure.dpi": 150,
            "savefig.dpi": 200,
        }
    )


def markdown_table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    headers = [label for _, label in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = [str(row.get(key, "")) for key, _ in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def did_cells(did) -> pd.DataFrame:
    y11 = float(did.details["treated_post"])
    y10 = float(did.details["treated_pre"])
    y01 = float(did.details["control_post"])
    y00 = float(did.details["control_pre"])
    control_change = y01 - y00
    counterfactual = y10 + control_change
    effect = y11 - counterfactual
    return pd.DataFrame(
        [
            {
                "series": "对照组",
                "period": "政策前",
                "mean_pm25": y00,
                "calculation_role": "observed",
                "note": "未限行城市政策前均值",
            },
            {
                "series": "对照组",
                "period": "政策后",
                "mean_pm25": y01,
                "calculation_role": "observed",
                "note": "用于估计共同时间变化",
            },
            {
                "series": "处理组",
                "period": "政策前",
                "mean_pm25": y10,
                "calculation_role": "observed",
                "note": "限行城市政策前均值",
            },
            {
                "series": "处理组",
                "period": "政策后",
                "mean_pm25": y11,
                "calculation_role": "observed",
                "note": "实际观察到的政策后均值",
            },
            {
                "series": "处理组反事实",
                "period": "政策后",
                "mean_pm25": counterfactual,
                "calculation_role": "counterfactual",
                "note": "处理组政策前均值 + 对照组前后变化",
            },
            {
                "series": "DID",
                "period": "政策后",
                "mean_pm25": effect,
                "calculation_role": "effect",
                "note": "实际处理组政策后 - 反事实处理组政策后",
            },
        ]
    )


def robustness_checks(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    did = simple_did(df, outcome="pm25", treated="treated_ever", post="post")
    rows.append(
        {
            "check": "四格 DID（全样本）",
            "estimate": did.estimate,
            "standard_error": None,
            "n_obs": did.n_obs,
            "interpretation": "主展示估计；没有模型标准误，仅作为透明计算。",
        }
    )

    twfe_weather = twfe_did(
        df,
        outcome="pm25",
        treatment="treatment",
        unit="city",
        time="month",
        covariates=["weather_index"],
        cluster="city",
    )
    rows.append(
        {
            "check": "TWFE + 天气控制",
            "estimate": twfe_weather.estimate,
            "standard_error": twfe_weather.standard_error,
            "n_obs": twfe_weather.n_obs,
            "interpretation": "加入城市固定效应、月份固定效应和天气控制。",
        }
    )

    twfe_no_weather = twfe_did(
        df,
        outcome="pm25",
        treatment="treatment",
        unit="city",
        time="month",
        covariates=[],
        cluster="city",
    )
    rows.append(
        {
            "check": "TWFE 不含天气控制",
            "estimate": twfe_no_weather.estimate,
            "standard_error": twfe_no_weather.standard_error,
            "n_obs": twfe_no_weather.n_obs,
            "interpretation": "检查结果是否主要由天气协变量设定驱动。",
        }
    )

    early = df[df["month"] <= 27].copy()
    early_twfe = twfe_did(
        early,
        outcome="pm25",
        treatment="treatment",
        unit="city",
        time="month",
        covariates=["weather_index"],
        cluster="city",
    )
    rows.append(
        {
            "check": "仅保留政策后 8 个月",
            "estimate": early_twfe.estimate,
            "standard_error": early_twfe.standard_error,
            "n_obs": early_twfe.n_obs,
            "interpretation": "检查短期窗口是否仍为负向。",
        }
    )

    placebo = df[df["month"] < 20].copy()
    placebo["placebo_post"] = (placebo["month"] >= 14).astype(int)
    placebo["placebo_treatment"] = placebo["treated_ever"] * placebo["placebo_post"]
    placebo_twfe = twfe_did(
        placebo,
        outcome="pm25",
        treatment="placebo_treatment",
        unit="city",
        time="month",
        covariates=["weather_index"],
        cluster="city",
    )
    rows.append(
        {
            "check": "提前 6 个月 placebo",
            "estimate": placebo_twfe.estimate,
            "standard_error": placebo_twfe.standard_error,
            "n_obs": placebo_twfe.n_obs,
            "interpretation": "只使用真实政策前数据；理想情况下应接近 0。",
        }
    )

    return pd.DataFrame(rows)


def plot_raw_trends(df: pd.DataFrame, path: Path, treatment_start: int) -> None:
    means = df.groupby(["month", "treated_ever"], as_index=False)["pm25"].mean()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for treated, label, color in [
        (1, "处理组（限行城市）", "#1f77b4"),
        (0, "对照组（未限行城市）", "#ff7f0e"),
    ]:
        sub = means[means["treated_ever"] == treated]
        ax.plot(sub["month"], sub["pm25"], marker="o", markersize=3, linewidth=1.8, label=label, color=color)
    ax.axvline(treatment_start, color="#5b8ea8", linestyle="--", linewidth=1.2)
    ax.text(treatment_start + 0.2, means["pm25"].max() - 0.4, f"政策实施 t={treatment_start}", fontsize=9)
    ax.set_title("原始趋势：处理组与对照组月度均值（DEMO DATA）")
    ax.set_xlabel("月份 month")
    ax.set_ylabel("PM2.5 均值")
    ax.grid(alpha=0.25)
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_four_cell_did(cells: pd.DataFrame, path: Path) -> None:
    def value(series: str, period: str) -> float:
        row = cells[(cells["series"] == series) & (cells["period"] == period)].iloc[0]
        return float(row["mean_pm25"])

    y00 = value("对照组", "政策前")
    y01 = value("对照组", "政策后")
    y10 = value("处理组", "政策前")
    y11 = value("处理组", "政策后")
    y_cf = value("处理组反事实", "政策后")
    did_value = value("DID", "政策后")

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.plot([0, 1], [y00, y01], marker="o", linewidth=2, label="对照组", color="#1f77b4")
    ax.plot([0, 1], [y10, y11], marker="o", linewidth=2, label="处理组（实际）", color="#ff7f0e")
    ax.plot([0, 1], [y10, y_cf], marker="o", linestyle="--", linewidth=2, label="处理组（反事实）", color="#2ca02c")
    ax.annotate(
        "",
        xy=(1.04, y_cf),
        xytext=(1.04, y11),
        arrowprops={"arrowstyle": "<->", "linewidth": 1.5, "color": "black"},
    )
    ax.text(1.07, (y_cf + y11) / 2, f"DID = {did_value:.2f}", va="center", fontsize=10)
    ax.set_xticks([0, 1], ["政策前", "政策后"])
    ax.set_ylabel("PM2.5 均值")
    ax.set_title("四格 DID：反事实与处理效应（DEMO DATA）")
    ax.grid(alpha=0.25)
    ax.legend(frameon=True, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_event_study(event: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    yerr = 1.96 * event["standard_error"].astype(float)
    ax.errorbar(
        event["event_time"],
        event["estimate"],
        yerr=yerr,
        marker="o",
        linestyle="none",
        capsize=3,
        color="#1f77b4",
    )
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(-1, color="#5b8ea8", linestyle="--", linewidth=1)
    ax.text(-0.9, event["estimate"].max(), "基准期 -1", fontsize=9)
    ax.set_title("事件研究系数 ±95% CI（DEMO DATA）")
    ax.set_xlabel("相对政策实施时间")
    ax.set_ylabel("系数估计")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_robustness(robustness: pd.DataFrame, path: Path) -> None:
    plot_data = robustness.dropna(subset=["standard_error"]).copy()
    plot_data = plot_data.iloc[::-1]
    y = range(len(plot_data))
    xerr = 1.96 * plot_data["standard_error"].astype(float)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.errorbar(plot_data["estimate"], y, xerr=xerr, marker="o", linestyle="none", capsize=3, color="#1f77b4")
    ax.axvline(0, color="black", linewidth=1)
    ax.set_yticks(list(y), plot_data["check"])
    ax.set_xlabel("估计值（负数表示 PM2.5 下降）")
    ax.set_title("稳健性与安慰剂检查（DEMO DATA）")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def render_demo_case_report(
    *,
    question: str,
    did,
    twfe,
    event: pd.DataFrame,
    cells: pd.DataFrame,
    robustness: pd.DataFrame,
    figure_dir: Path,
) -> str:
    treated_cities = 6
    n_cities = 24
    n_months = 36
    treatment_start = 20
    true_effect = -2.0
    y00 = float(did.details["control_pre"])
    y01 = float(did.details["control_post"])
    y10 = float(did.details["treated_pre"])
    y11 = float(did.details["treated_post"])
    counterfactual = y10 + (y01 - y00)

    cell_rows = []
    for _, row in cells.iterrows():
        cell_rows.append(
            {
                "series": row["series"],
                "period": row["period"],
                "mean_pm25": fmt(row["mean_pm25"]),
                "role": row["calculation_role"],
                "note": row["note"],
            }
        )

    robust_rows = []
    for _, row in robustness.iterrows():
        se = row["standard_error"]
        ci = ""
        if not pd.isna(se):
            ci = f"[{float(row['estimate']) - 1.96 * float(se):.3f}, {float(row['estimate']) + 1.96 * float(se):.3f}]"
        robust_rows.append(
            {
                "check": row["check"],
                "estimate": fmt(row["estimate"]),
                "se": "" if pd.isna(se) else fmt(se),
                "ci": ci,
                "n_obs": int(row["n_obs"]),
                "interpretation": row["interpretation"],
            }
        )

    lead_rows = []
    for _, row in event[event["event_time"] < 0].iterrows():
        lead_rows.append(
            {
                "event_time": int(row["event_time"]),
                "estimate": fmt(row["estimate"]),
                "se": fmt(row["standard_error"]),
            }
        )
    lag_rows = []
    for _, row in event[event["event_time"] >= 0].iterrows():
        lag_rows.append(
            {
                "event_time": int(row["event_time"]),
                "estimate": fmt(row["estimate"]),
                "se": fmt(row["standard_error"]),
            }
        )

    return f"""# 8 端到端案例：城市限行政策对 PM2.5 的影响

为了展示完整链路，本 demo 使用合成数据：{n_cities} 个城市、{n_months} 个月、{treated_cities} 个处理城市，政策在第 {treatment_start} 个月实施，数据生成时设定的真实处理效应为 {true_effect:.1f}。特别说明：这些结果只用于验证工作流、图表和报告产出，不构成任何真实政策结论。

## 8.0 从问题到报告的操作链路

本案例完整还原了系统应当执行的步骤，而不是只给一个回归结果。

1. 明确政策问题：{question}
2. 定义 estimand：处理城市在政策实施后的平均处理效应，近似为 post-period ATT。
3. 构造面板数据：单位是 city-month，结果变量是 `pm25`，处理变量是 `treatment = treated_ever × post`。
4. 方法路由：因为有处理组、对照组、政策前后和面板结构，主方法选择 DID，并用 event study 检查动态效应和预趋势。
5. 先画 raw trends：在回归前检查处理组和对照组政策前走势是否大体可比。
6. 计算四格 DID：把“如果没有政策，处理组会怎样”明确写成反事实均值。
7. 跑 TWFE DID：加入城市固定效应、月份固定效应和天气控制，作为基线回归。
8. 跑 event study：展示政策前 lead 和政策后 lag，不只报告一个点估计。
9. 做稳健性和 placebo：检查窗口、协变量和提前政策时点是否改变结论。
10. 输出复现文件：数据、估计 JSON、DID 中间表、事件研究表、稳健性表、图片和 Markdown 报告。

## 8.1 原始趋势：先看平行趋势

DID 的第一步不是直接跑回归，而是先画 raw trends。图中可以看到处理组和对照组在政策前总体同向波动，政策后处理组均值更低。不过这只是目视检查，不能单独证明平行趋势成立。

![图 1. 原始趋势图（DEMO DATA）：处理组与对照组 PM2.5 月度均值。]({figure_dir.name}/demo_raw_trends.png)

图 1. 原始趋势图（DEMO DATA）：处理组与对照组 PM2.5 月度均值。虚线是政策实施月份 t={treatment_start}。

## 8.2 DID：把反事实讲清楚

DID 的直觉是：如果没有限行政策，处理组在政策后的变化应当和对照组类似。因此先把对照组的前后变化平移到处理组，得到处理组的反事实终点；实际终点和反事实终点之间的差，就是 DID 估计。

四格均值如下：

{markdown_table(cell_rows, [("series", "序列"), ("period", "时期"), ("mean_pm25", "PM2.5 均值"), ("role", "角色"), ("note", "说明")])}

计算过程：

```text
对照组变化 = {y01:.3f} - {y00:.3f} = {y01 - y00:.3f}
处理组反事实政策后 = {y10:.3f} + ({y01:.3f} - {y00:.3f}) = {counterfactual:.3f}
DID = 处理组实际政策后 - 处理组反事实政策后
    = {y11:.3f} - {counterfactual:.3f}
    = {did.estimate:.3f}
```

![图 2. 四格 DID（DEMO DATA）：对照组变化被平移为处理组反事实。]({figure_dir.name}/demo_four_cell_did.png)

图 2. 四格 DID（DEMO DATA）：对照组变化被平移为处理组反事实。本 demo 中四格 DID 为 {did.estimate:.2f}，方向与设定的真实效应 {true_effect:.1f} 一致。

## 8.3 事件研究：动态效应与预趋势诊断

事件研究把 DID 拆成相对政策实施时间的动态系数。它有两个作用：第一，看政策前的 lead 是否接近 0，用来诊断预趋势；第二，看政策后的 lag 是否逐步转负或保持负向，用来描述动态效应。

![图 3. 事件研究系数 ±95% CI（DEMO DATA）。]({figure_dir.name}/demo_event_study.png)

图 3. 事件研究系数 ±95% CI（DEMO DATA）。基准期是 event time = -1。由于这是小型 demo，政策前系数并不完全贴近 0，这正好说明系统不能只看一个 DID 点估计，必须把诊断结果一起呈现。

政策前 lead：

{markdown_table(lead_rows, [("event_time", "event time"), ("estimate", "估计值"), ("se", "标准误")])}

政策后 lag：

{markdown_table(lag_rows, [("event_time", "event time"), ("estimate", "估计值"), ("se", "标准误")])}

## 8.4 基线回归：TWFE DID

在四格 DID 之后，系统进一步运行两维固定效应回归：

```text
pm25 ~ treatment + C(city) + C(month) + weather_index
```

这个设定控制了城市不随时间变化的差异、所有城市共同面对的月份冲击，以及 demo 中模拟的天气指标。TWFE 估计值为 `{twfe.estimate:.3f}`，聚类标准误为 `{twfe.standard_error:.3f}`，样本量为 `{twfe.n_obs}`。

## 8.5 稳健性、安慰剂与诊断结果

完整案例不能只放一个回归表，还要展示检查链路。下面的表把主要估计、协变量敏感性、窗口敏感性和 placebo timing 放在一起。

{markdown_table(robust_rows, [("check", "检查"), ("estimate", "估计值"), ("se", "标准误"), ("ci", "95% CI"), ("n_obs", "样本量"), ("interpretation", "解释")])}

![图 4. 稳健性与安慰剂检查（DEMO DATA）。]({figure_dir.name}/demo_robustness.png)

图 4. 稳健性与安慰剂检查（DEMO DATA）。负值表示 PM2.5 下降。placebo 只使用真实政策前数据，因此它不是政策效果，而是预趋势/伪政策诊断。

## 8.6 结果解释：能说什么，不能说什么

在这个 demo 中，四格 DID 为 `{did.estimate:.3f}`，TWFE DID 为 `{twfe.estimate:.3f}`，都指向政策后处理组 PM2.5 相对下降。因为数据生成时真实效应为 {true_effect:.1f}，结果用于说明工作流能够恢复大致方向。

但这不是一条真实政策结论。真实研究还需要核验政策发布日期、生效日、执行强度、豁免规则、监测站口径、气象冲击、产业变化、跨城市污染转移和相邻城市溢出。如果预趋势诊断不过关，应该降级为设计讨论或重新寻找对照组，而不是强行解释 DID。

## 8.7 复现清单

运行命令：

```bash
python scripts/run_demo_analysis.py
```

本次脚本会生成或更新：

- `examples/data/demo_panel.csv`：合成 city-month 面板数据。
- `examples/outputs/demo_estimates.json`：四格 DID 和 TWFE DID 估计。
- `examples/outputs/demo_did_cells.csv`：四格 DID 与反事实计算中间表。
- `examples/outputs/demo_event_study.csv`：事件研究系数。
- `examples/outputs/demo_robustness.csv`：稳健性和 placebo 检查。
- `examples/outputs/figures/demo_raw_trends.png`：原始趋势图。
- `examples/outputs/figures/demo_four_cell_did.png`：四格 DID 反事实图。
- `examples/outputs/figures/demo_event_study.png`：事件研究图。
- `examples/outputs/figures/demo_robustness.png`：稳健性图。
- `examples/outputs/demo_report.md`：本完整案例报告。
"""


def main() -> int:
    data_path = ROOT / "examples" / "data" / "demo_panel.csv"
    out_dir = ROOT / "examples" / "outputs"
    figure_dir = out_dir / "figures"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    configure_plots()

    df = generate_demo_panel()
    df.to_csv(data_path, index=False)

    question = "某城市交通限行政策是否降低 PM2.5？我们有城市-月份面板数据、政策前后、多个未限行城市。"
    recs = recommend_methods(question, metadata={"data_structure": "panel", "treatment_timing": "before/after", "unit_of_observation": "city-month"})
    did = simple_did(df, outcome="pm25", treated="treated_ever", post="post")
    twfe = twfe_did(df, outcome="pm25", treatment="treatment", unit="city", time="month", covariates=["weather_index"], cluster="city")
    event = event_study_coefficients(df, outcome="pm25", event_time="event_time", unit="city", time="month", treated_ever="treated_ever", window=(-5, 5))
    event.to_csv(out_dir / "demo_event_study.csv", index=False)
    cells = did_cells(did)
    cells.to_csv(out_dir / "demo_did_cells.csv", index=False)
    robustness = robustness_checks(df)
    robustness.to_csv(out_dir / "demo_robustness.csv", index=False)

    plot_raw_trends(df, figure_dir / "demo_raw_trends.png", treatment_start=20)
    plot_four_cell_did(cells, figure_dir / "demo_four_cell_did.png")
    plot_event_study(event, figure_dir / "demo_event_study.png")
    plot_robustness(robustness, figure_dir / "demo_robustness.png")

    write_json(
        out_dir / "demo_estimates.json",
        {
            "metadata": {
                "demo_data": True,
                "n_cities": 24,
                "n_months": 36,
                "treated_cities": 6,
                "treatment_start": 20,
                "true_effect": -2.0,
                "warning": "Synthetic demo data. Do not interpret as real policy evidence.",
            },
            "simple_did": did.to_dict(),
            "twfe": twfe.to_dict(),
        },
    )
    report = render_demo_case_report(
        question=question,
        did=did,
        twfe=twfe,
        event=event,
        cells=cells,
        robustness=robustness,
        figure_dir=figure_dir.relative_to(out_dir),
    )
    write_markdown_report(out_dir / "demo_report.md", report)
    print(f"Demo data: {data_path}")
    print(f"Demo report: {out_dir / 'demo_report.md'}")
    print(f"Demo figures: {figure_dir}")
    print(f"TWFE estimate: {twfe.estimate:.3f} (se={twfe.standard_error:.3f})")
    print(f"Method recommendation: {recs[0].method if recs else 'none'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
