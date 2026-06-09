from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable
import re


@dataclass
class MethodRecommendation:
    method: str
    priority: int
    why: str
    required_data: list[str]
    identifying_assumptions: list[str]
    estimators: list[str]
    diagnostics: list[str]
    failure_modes: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_KEYWORDS = {
    "did": [
        "did", "diff-in-diff", "difference-in-differences", "双重差分", "差分", "事件研究", "event study",
        "staggered", "分批", "政策前后", "处理组", "对照组", "面板", "panel", "城市", "州", "省份",
    ],
    "synthetic_control": [
        "synthetic control", "合成控制", "single treated", "单一处理", "个案", "一个城市", "一个州",
        "donor", "counterfactual unit", "比较城市",
    ],
    "iv": [
        "instrument", "instrumental", "iv", "工具变量", "鼓励", "encouragement", "random assignment",
        "lottery", "抽签", "cutoff instrument",
    ],
    "rdd": [
        "rdd", "regression discontinuity", "断点", "阈值", "cutoff", "门槛", "分数线", "年龄线",
        "eligibility threshold",
    ],
    "matching": [
        "matching", "propensity", "倾向得分", "匹配", "observational", "可观测混杂", "selection on observables",
    ],
    "dml": [
        "dml", "double machine learning", "double/debiased", "高维", "high-dimensional", "many controls",
        "nuisance", "cross-fitting", "elastic net", "random forest controls",
    ],
    "causal_forest": [
        "heterogeneous", "异质性", "who benefits", "谁受益", "treatment effect heterogeneity",
        "causal forest", "grf", "generalized random forest", "uplift", "个体化",
    ],
    "policy_learning": [
        "targeting", "资源分配", "policy learning", "最优政策", "optimal policy", "treatment assignment",
        "预算约束", "welfare", "who should receive",
    ],
    "rct": [
        "rct", "randomized", "随机实验", "实验", "a/b test", "ab test", "field experiment", "pilot randomized",
    ],
}


_METHOD_LIBRARY: dict[str, dict[str, Any]] = {
    "rct": {
        "name": "随机实验 / A/B test / field experiment",
        "why": "当处理分配可以被随机化或已有随机试点时，这是最直接的识别策略。",
        "required_data": ["随机分配机制", "处理状态", "结果变量", "基线变量", "不合规/流失记录"],
        "identifying_assumptions": ["随机分配独立于潜在结果", "SUTVA/无干扰", "样本流失不系统性改变比较", "执行记录可靠"],
        "estimators": ["均值差", "协变量调整 OLS", "ITT/TOT", "分层或聚类稳健标准误"],
        "diagnostics": ["基线平衡", "流失平衡", "实验执行审计", "多重检验控制"],
        "failure_modes": ["溢出效应", "不遵从", "选择性流失", "样本过小"],
        "next_actions": ["确认随机化单位和合规情况", "绘制 CONSORT/样本流图", "预注册主要结果和异质性分析"],
    },
    "did": {
        "name": "双重差分 DID / event-study / staggered adoption",
        "why": "适合政策前后、处理组与对照组、面板或重复截面数据的问题。",
        "required_data": ["单位 ID", "时间 ID", "处理开始时间", "结果变量", "处理前后协变量", "潜在对照组"],
        "identifying_assumptions": ["平行趋势", "无预期效应或可建模", "无严重溢出", "构成变化可控", "处理时间记录准确"],
        "estimators": ["两维固定效应 TWFE", "Sun-Abraham / Callaway-Sant'Anna 风格分组时间 ATT", "事件研究", "聚类稳健标准误"],
        "diagnostics": ["处理前趋势图", "placebo leads", "事件时间系数", "平衡性和样本构成检查", "不同对照组敏感性"],
        "failure_modes": ["处理效应异质且 staggered TWFE 权重异常", "政策前已有趋势差异", "同时发生的政策冲击", "跨地区溢出"],
        "next_actions": ["先画 raw trends", "定义 never-treated 或 not-yet-treated 对照组", "写明处理日期和事件窗口", "规划 placebo 与 alternative controls"],
    },
    "synthetic_control": {
        "name": "合成控制 / matrix completion / synthetic DID",
        "why": "适合一个或少数地区/组织在明确时间点受到政策影响，并存在一组可比 donor units。",
        "required_data": ["处理单位", "donor pool", "足够长的政策前结果序列", "政策时间", "协变量或预测变量"],
        "identifying_assumptions": ["donor pool 可以组合出处理前轨迹", "无 donor 污染", "干预前拟合良好", "没有同时间专属冲击"],
        "estimators": ["经典 synthetic control", "augmented synthetic control", "synthetic DID", "matrix completion"],
        "diagnostics": ["政策前 RMSPE", "placebo-in-space", "placebo-in-time", "leave-one-out donor", "donor weights 审查"],
        "failure_modes": ["处理前拟合差", "donor pool 受污染", "单个 donor 权重过高", "政策同时伴随其他冲击"],
        "next_actions": ["审查 donor pool 合理性", "比较处理前轨迹", "运行 placebo distribution", "报告 gap 与不确定性而非只报告点估计"],
    },
    "iv": {
        "name": "工具变量 IV / encouragement design",
        "why": "当处理内生，但存在影响处理、且不直接影响结果的外生变异时优先考虑。",
        "required_data": ["工具变量 Z", "处理变量 D", "结果变量 Y", "协变量", "一阶段强度证据"],
        "identifying_assumptions": ["相关性", "排除限制", "独立性", "单调性", "LATE 解释"],
        "estimators": ["2SLS", "LATE", "弱工具稳健推断", "DML-IV/orthogonal IV"],
        "diagnostics": ["一阶段 F 统计", "reduced form", "平衡性", "over-identification 如果有多个工具", "机制和排除限制论证"],
        "failure_modes": ["弱工具", "工具直接影响结果", "违反单调性", "LATE 人群过窄"],
        "next_actions": ["画出 Z→D→Y 的 DAG", "准备排除限制反驳清单", "先估 reduced form 和 first stage", "解释 compliers"],
    },
    "rdd": {
        "name": "断点回归 RDD / fuzzy RDD",
        "why": "当政策资格或处理由阈值规则决定时，断点附近可形成局部准实验。",
        "required_data": ["running variable", "cutoff", "处理状态", "结果变量", "断点附近样本", "协变量"],
        "identifying_assumptions": ["阈值附近无法精确操纵", "潜在结果在 cutoff 连续", "局部样本可比", "带宽选择合理"],
        "estimators": ["local linear RDD", "bias-corrected RDD", "fuzzy RDD/IV", "donut RDD"],
        "diagnostics": ["McCrary density", "协变量连续性", "带宽敏感性", "多项式阶数敏感性", "donut 检查"],
        "failure_modes": ["running variable 被操纵", "断点附近其他政策同时变化", "带宽选择驱动结论", "局部效应无法外推"],
        "next_actions": ["确认 cutoff 规则", "画 binscatter", "运行密度和协变量平衡检查", "报告局部解释范围"],
    },
    "matching": {
        "name": "匹配 / 倾向得分 / weighting under selection-on-observables",
        "why": "适合没有明确准实验，但有丰富处理前协变量且想构造可比样本的观察性研究。",
        "required_data": ["处理前协变量", "处理状态", "结果变量", "共同支持区域", "样本权重"],
        "identifying_assumptions": ["可观测变量条件下无混杂", "重叠/positivity", "协变量在处理前测量", "SUTVA"],
        "estimators": ["propensity score matching", "IPW", "entropy balancing", "doubly robust AIPW"],
        "diagnostics": ["标准化差异", "共同支持", "权重极端值", "未观测混杂敏感性"],
        "failure_modes": ["关键未观测混杂", "重叠差", "bad controls", "post-treatment controls"],
        "next_actions": ["列出所有混杂路径", "只使用处理前协变量", "检查 balance 和 overlap", "规划 Rosenbaum/E-value 风格敏感性分析"],
    },
    "dml": {
        "name": "Double Machine Learning / orthogonal ML",
        "why": "适合高维协变量、复杂 nuisance function，目标仍是低维平均处理效应或政策参数。",
        "required_data": ["处理变量", "结果变量", "高维处理前协变量", "足够样本量", "交叉拟合 folds"],
        "identifying_assumptions": ["条件可忽略性或明确 orthogonal moment", "重叠", "nuisance 模型足够稳定", "样本独立或聚类结构可处理"],
        "estimators": ["partialling-out DML", "DML-IRM", "DML-IV", "AIPW with ML nuisances"],
        "diagnostics": ["cross-fitting 稳定性", "propensity overlap", "nuisance out-of-sample performance", "learner sensitivity"],
        "failure_modes": ["重叠不足", "样本太小导致 ML 不稳定", "目标 estimand 与模型不一致", "未观测混杂"],
        "next_actions": ["明确 estimand", "选择 2-3 个 baseline learners", "固定随机种子和 folds", "报告 learner sensitivity"],
    },
    "causal_forest": {
        "name": "因果森林 / generalized random forests / CATE",
        "why": "适合关注处理效应异质性、分群、targeting，而不仅是平均效应。",
        "required_data": ["处理变量", "结果变量", "丰富协变量", "足够样本", "重叠区域", "政策可行动特征"],
        "identifying_assumptions": ["条件可忽略性或实验分配", "honesty/sample splitting", "重叠", "异质性解释不过度外推"],
        "estimators": ["causal forest", "GRF", "R-learner", "DR-learner", "uplift model"],
        "diagnostics": ["CATE calibration", "RATE/TOC", "分组 ATE", "变量重要性谨慎解释", "policy value evaluation"],
        "failure_modes": ["把预测异质性误解为因果机制", "多重挖掘", "重叠不足", "行动变量不合法/不公平"],
        "next_actions": ["先估平均效应", "定义可行动 subgroup", "使用 honest splitting", "用 holdout 评估 policy value"],
    },
    "policy_learning": {
        "name": "Policy learning / treatment targeting / welfare maximization",
        "why": "适合从估计处理效应转向资源配置、政策 targeting 或预算约束下的决策规则。",
        "required_data": ["处理效应估计或实验/准实验数据", "成本", "预算约束", "可行动特征", "公平性约束"],
        "identifying_assumptions": ["用于学习的效应可迁移到部署环境", "成本和福利定义透明", "约束可执行", "评估集独立"],
        "estimators": ["policy tree", "doubly robust policy value", "offline policy evaluation", "cost-sensitive targeting"],
        "diagnostics": ["holdout policy value", "subgroup welfare", "fairness audit", "budget sensitivity", "implementation feasibility"],
        "failure_modes": ["过拟合 policy rule", "忽略成本/公平性", "训练环境与部署环境漂移", "未识别的效应被拿去优化"],
        "next_actions": ["先确认因果识别已站住", "定义 welfare 和约束", "分训练/验证/评估集", "报告不实施/全实施/目标化三种基线"],
    },
}


_DEFAULT_FALLBACK = ["policy_evaluation_intake", "dag_identification", "matching", "dml"]


def _normalize_text(parts: Iterable[Any]) -> str:
    return " ".join(str(p or "") for p in parts).lower()


def _keyword_score(text: str, key: str) -> int:
    score = 0
    for kw in _KEYWORDS.get(key, []):
        if kw.lower() in text:
            score += 2 if len(kw) > 5 else 1
    return score


def _structural_score(metadata: dict[str, Any], key: str) -> int:
    score = 0
    data_structure = str(metadata.get("data_structure", "")).lower()
    treatment_timing = str(metadata.get("treatment_timing", "")).lower()
    assignment = str(metadata.get("assignment_mechanism", "")).lower()
    unit = str(metadata.get("unit_of_observation", "")).lower()
    n_treated = str(metadata.get("number_of_treated_units", "")).lower()

    if key == "did" and any(x in data_structure for x in ["panel", "面板", "repeated"]):
        score += 4
    if key == "did" and any(x in treatment_timing for x in ["before", "after", "staggered", "政策前后", "分批"]):
        score += 3
    if key == "synthetic_control" and any(x in n_treated for x in ["1", "one", "single", "一个"]):
        score += 4
    if key == "rct" and any(x in assignment for x in ["random", "随机", "lottery", "a/b"]):
        score += 5
    if key == "iv" and any(x in assignment for x in ["instrument", "encouragement", "lottery", "工具"]):
        score += 4
    if key == "rdd" and any(x in assignment for x in ["cutoff", "threshold", "断点", "阈值"]):
        score += 5
    if key in {"causal_forest", "policy_learning"} and any(x in unit for x in ["individual", "person", "household", "firm", "个人", "家庭", "企业"]):
        score += 1
    return score


def recommend_methods(
    question: str,
    *,
    metadata: dict[str, Any] | None = None,
    top_k: int = 4,
) -> list[MethodRecommendation]:
    """Recommend causal designs for a policy-evaluation question.

    The router is deliberately transparent and rules-based. Codex agents can use
    this as a first pass, then override it after reading data, literature, and
    context.
    """
    metadata = metadata or {}
    text = _normalize_text([question, *metadata.values()])
    scores: dict[str, int] = {}
    for key in _METHOD_LIBRARY:
        scores[key] = _keyword_score(text, key) + _structural_score(metadata, key)

    # Lightweight interactions between clues.
    if scores["did"] > 0 and scores["synthetic_control"] > 0:
        scores["synthetic_control"] += 1
    if scores["dml"] > 0 and scores["causal_forest"] > 0:
        scores["causal_forest"] += 1
    if scores["causal_forest"] > 0 and scores["policy_learning"] > 0:
        scores["policy_learning"] += 1

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    chosen = [(k, s) for k, s in ranked if s > 0][:top_k]
    if not chosen:
        chosen = [("matching", 1), ("dml", 1), ("did", 1), ("synthetic_control", 1)][:top_k]

    recommendations: list[MethodRecommendation] = []
    for rank, (key, score) in enumerate(chosen, start=1):
        item = _METHOD_LIBRARY[key]
        recommendations.append(
            MethodRecommendation(
                method=item["name"],
                priority=rank,
                why=f"{item['why']} 路由得分={score}。",
                required_data=list(item["required_data"]),
                identifying_assumptions=list(item["identifying_assumptions"]),
                estimators=list(item["estimators"]),
                diagnostics=list(item["diagnostics"]),
                failure_modes=list(item["failure_modes"]),
                next_actions=list(item["next_actions"]),
            )
        )
    return recommendations


def recommendations_to_markdown(recommendations: list[MethodRecommendation]) -> str:
    lines = ["# 方法推荐", ""]
    for rec in recommendations:
        lines.append(f"## {rec.priority}. {rec.method}")
        lines.append(f"**为什么**：{rec.why}")
        lines.append("**需要的数据**：" + "；".join(rec.required_data))
        lines.append("**识别假设**：" + "；".join(rec.identifying_assumptions))
        lines.append("**估计器**：" + "；".join(rec.estimators))
        lines.append("**诊断**：" + "；".join(rec.diagnostics))
        lines.append("**失败模式**：" + "；".join(rec.failure_modes))
        lines.append("**下一步**：" + "；".join(rec.next_actions))
        lines.append("")
    return "\n".join(lines)


def infer_metadata_from_text(question: str) -> dict[str, str]:
    """Very small heuristic helper used by the CLI."""
    q = question.lower()
    meta: dict[str, str] = {}
    if re.search(r"面板|panel|城市|county|state|province|月份|monthly|year", q):
        meta["data_structure"] = "panel"
    if re.search(r"政策前后|before|after|pre|post|event|事件", q):
        meta["treatment_timing"] = "before/after"
    if re.search(r"随机|random|lottery|抽签|a/b", q):
        meta["assignment_mechanism"] = "randomized"
    if re.search(r"阈值|断点|cutoff|threshold", q):
        meta["assignment_mechanism"] = "cutoff"
    if re.search(r"工具变量|instrument|encouragement", q):
        meta["assignment_mechanism"] = "instrument"
    if re.search(r"一个城市|one city|single|单一", q):
        meta["number_of_treated_units"] = "single"
    return meta
