# Prompt 02 — 多 agent 评估

```text
请启动 subagents：policy_source_scout、policy_document_processor、event_scout、method_router_agent、identification_auditor、data_engineer_agent、robustness_reviewer、policy_translator。

任务：[粘贴政策问题]

要求：
- policy_source_scout：找权威政策来源和数据来源，列出需要核验的事实。
- policy_document_processor：如果本地已有政策文件，抽取时间线、适用范围、处理强度和 treatment coding；如果没有文件，输出待收集文件清单。
- event_scout：判断该事件是否有研究价值和可行反事实。
- method_router_agent：推荐主方法和备选方法。
- identification_auditor：审查 DAG、识别假设、溢出、预期效应和同期政策。
- data_engineer_agent：设计 unit-time 数据结构、merge key、字段和数据质量检查。
- robustness_reviewer：提出反方审查、placebo、负向控制和敏感性分析。
- policy_translator：说明政策含义、外推限制和不能声称的内容。

每个 agent 独立输出核心判断、主要风险、下一步行动。最后由你汇总成一页 research triage memo，并列出需要人工核验的政策事实。
```
