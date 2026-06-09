from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import textwrap

from .method_router import MethodRecommendation, recommendations_to_markdown
from .estimators import EstimateResult


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def render_evaluation_report(
    *,
    title: str,
    question: str,
    recommendations: list[MethodRecommendation],
    estimates: list[EstimateResult] | None = None,
    limitations: list[str] | None = None,
) -> str:
    estimates = estimates or []
    limitations = limitations or [
        "该报告基于示例或当前可用数据，不应被解释为最终政策结论。",
        "任何因果结论都依赖识别假设；需要结合制度背景、数据质量和稳健性检查。",
    ]
    lines: list[str] = [
        f"# {title}",
        "",
        "## 1. 政策问题",
        question,
        "",
        "## 2. 推荐识别策略",
        "",
    ]
    lines.append(recommendations_to_markdown(recommendations).replace("# 方法推荐\n\n", ""))
    if estimates:
        lines.extend(["", "## 3. 基线估计结果", ""])
        for est in estimates:
            se = "NA" if est.standard_error is None else f"{est.standard_error:.4f}"
            lines.append(f"- **{est.method}**：估计值 `{est.estimate:.4f}`，标准误 `{se}`，样本量 `{est.n_obs}`。")
            if est.details:
                detail = "; ".join(f"{k}={v}" for k, v in est.details.items())
                lines.append(f"  - details: {detail}")
    lines.extend(["", "## 4. 必做稳健性与敏感性", ""])
    for item in [
        "识别假设反驳表：逐条列出最可能破坏识别的机制。",
        "替代样本、替代对照组、替代结果变量。",
        "placebo timing / placebo units。",
        "预趋势或断点/工具变量/重叠等设计特定诊断。",
        "把统计显著性、效应大小、政策成本和可执行性分开报告。",
    ]:
        lines.append(f"- {item}")
    lines.extend(["", "## 5. 局限", ""])
    for lim in limitations:
        lines.append(f"- {lim}")
    lines.extend(["", "## 6. Codex 复现提示", "", textwrap.dedent("""
    在 Codex 中继续分析时，建议执行：

    ```text
    /skills
    使用 causal-method-router、did-event-study、robustness-sensitivity、replication-report 四个 skills。
    请先生成 design card，再运行 baseline estimator，最后让 robustness_reviewer subagent 审查识别假设。
    ```
    """).strip()])
    return "\n".join(lines) + "\n"


def write_markdown_report(path: str | Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
