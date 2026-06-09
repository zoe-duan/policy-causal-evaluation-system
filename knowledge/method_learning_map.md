# 方法学习地图：因果推断与政策评估

本文件把系统需要掌握的因果推断知识组织成可执行的 Codex 工作流。它只保留方法论结构、适用条件、诊断要求和实现路径，不依赖或引用任何外部方法体系名称。

## 方法主题 → 系统模块

| 方法主题 | 系统对应文件/技能 | 系统用途 |
|---|---|---|
| 因果图、识别、控制变量选择 | `$causal-dag-identification`、`knowledge/causal_roadmap.md` | 明确 estimand、DAG、调整集、bad controls、spillovers |
| 实验与鼓励设计 | `knowledge/method_matrix.md` | 处理随机分配、cluster rollout、compliance 和 ITT/TOT |
| 匹配、倾向得分、回归调整 | `knowledge/method_matrix.md`、`src/causal_policy_system/method_router.py` | 选择基于可观测变量的识别路线 |
| 双重差分与事件研究 | `$did-event-study`、`R/did_template.R` | 面板政策冲击、动态效应、pre-trends、错位实施风险 |
| 合成控制和矩阵补全思路 | `$synthetic-control` | 单个或少数处理单位、donor pool、pre-fit 和 placebo |
| 工具变量与断点设计 | `$iv-rdd-design` | LATE、弱工具变量、排他性约束、阈值政策和 manipulation 检查 |
| 双重/去偏机器学习 | `$dml-doubly-robust`、`R/doubleml_template.R` | 高维协变量、nuisance models、orthogonal score、cross-fitting |
| 异质性效应和政策学习 | `$causal-forest-policy-learning`、`R/grf_template.R` | CATE、GRF/causal forest、policy value、targeting 和公平性 |
| 稳健性和敏感性分析 | `$robustness-sensitivity` | 安慰剂、负向控制、窗口敏感性、donor/带宽/协变量敏感性 |
| 政策文件搜集与制度事实抽取 | `$policy-source-scout`、`$policy-document-processor` | 找权威政策来源、抽取发布日期/生效日/适用范围/执行机制 |

## 系统约束

1. 任何 estimator 都不能替代 identification。先判断反事实来源，再谈模型。
2. 文本中的“政策实施日期”必须区分：发布日、通过日、生效日、执行日、试点日、废止/修订日。
3. 政策文件和数据源要建立证据链：来源层级、URL/文件名、访问日期、原文摘录、抽取字段、抽取不确定性。
4. 机器学习方法只在识别假设可辩护时使用；DML/DR/GRF 负责高维控制和异质性，不自动解决未观测混杂。
5. 报告中必须把结论标成 `strong`、`moderate`、`weak` 或 `design-only`。

## 推荐启动提示

```text
请先阅读 AGENTS.md、knowledge/method_learning_map.md、knowledge/method_matrix.md、knowledge/policy_document_processing.md。
把我的政策问题转成 design card，先给出政策文件搜集计划，再推荐 2-3 个可行识别方法。
```
