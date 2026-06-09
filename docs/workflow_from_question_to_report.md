# 从问题到报告的工作流

## 1. 新问题进入

填写 `templates/intake_questionnaire.md` 或直接使用 `prompts/01_new_policy_question.md`。

产物：
- 因果问题重写；
- treatment/outcome/unit/time；
- estimand；
- 数据需求；
- 初步方法推荐。

## 2. 方法路由

使用 `causal-method-router` skill 和 `scripts/causal_policy_cli.py recommend`。

优先级规则：
- 随机化 → RCT/ITT/TOT；
- 政策前后 + 处理/对照 + 面板 → DID/event-study；
- 单个或少数处理单位 + 长政策前序列 → synthetic control；
- 阈值分配 → RDD；
- 外生工具/鼓励 → IV；
- 高维协变量 → DML；
- 异质性/targeting → causal forest/policy learning。

## 3. Design card

每个研究必须有 `design_card.yaml`。没有 design card 时，不允许直接报告“政策有效/无效”。

## 4. 数据与估计

先运行最小 estimator，再做设计特定诊断。估计脚本应保存到 `studies/[slug]/scripts`，输出保存到 `studies/[slug]/outputs`。

## 5. 稳健性和审查

使用 `robustness_reviewer` subagent 从反对者角度找漏洞。报告必须包含至少一个可能推翻结论的威胁。

## 6. 报告

用 `templates/evaluation_report.md` 或 `scripts/render_report.py` 生成报告。报告必须明确：估计的是哪个 estimand；结论依赖哪些假设；哪些问题不能从当前数据回答。
