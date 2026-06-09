# 方法知识内核

本文件把系统应掌握的因果推断与政策评估方法压缩成可执行的 Codex 工作记忆。它不依赖单一外部材料；Codex 在具体研究中应结合最新文献、政策原文和数据质量重新判断。

## 方法主题 → 系统模块

| 方法主题 | 系统对应文件/技能 | 系统用途 |
|---|---|---|
| 潜在结果、DAG、识别假设 | `$causal-dag-identification`、`knowledge/causal_roadmap.md` | 明确 estimand、混杂、选择、bad controls、溢出和可识别性 |
| 实验与准实验设计 | `$policy-evaluation-intake`、`$causal-method-router` | 把政策问题转成可验证的研究设计 |
| DID、动态 event study、错位实施 | `$did-event-study` | 处理政策前后和分批实施的面板设计 |
| Synthetic control、synthetic DID、matrix completion | `$synthetic-control` | 少数处理单位和 aggregate policy shock |
| IV、RDD、鼓励设计、阈值政策 | `$iv-rdd-design` | 处理工具变量、资格阈值、LATE 与局部识别 |
| 高维协变量、cross-fitting、正交化 | `$dml-doubly-robust` | 在选择基于可观测变量时降低模型偏误 |
| 因果森林、GRF、CATE、policy learning | `$causal-forest-policy-learning` | 异质性、目标化政策和福利比较 |
| 稳健性、安慰剂、敏感性 | `$robustness-sensitivity` | 对主要识别假设做反证和压力测试 |
| 政策发现、政策原文处理、证据日志 | `$policy-document-intake`、`$event-research-scout` | 从政策文本中提取事件时间、适用范围、强度和可验证出处 |

## 系统约束

1. 先识别，后估计；方法选择必须服从数据生成过程和政策制度细节。
2. 对任何“政策有效吗”的问题，先写清楚反事实：没有政策时，同一对象会怎样。
3. 对 DID/event study，不能只跑 TWFE；必须检查趋势、处理时点、异质性权重、never-treated/not-yet-treated 对照定义。
4. 对 ML 因果方法，不能把预测性能等同于因果识别；必须说明 overlap、nuisance learning、cross-fitting、样本切分和不确定性。
5. 对 CATE/policy learning，必须把效应发现、规则学习和外部验证分开。
6. 对政策文本，必须优先记录原始出处、发布日期/生效日期、发布机构、适用范围、政策强度、修订/废止信息和镜像备份。

## 推荐默认提示

```text
请根据 knowledge/method_playbook.md、knowledge/method_matrix.md、knowledge/policy_source_inventory.md 和 knowledge/policy_document_processing.md，把我的问题转成 design card，并推荐 2-3 个可行方法。不要跳过政策原文核验和证据日志。
```
