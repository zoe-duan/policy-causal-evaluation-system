# Prompt 04 — 执行分析

```text
请读取 studies/[slug]/design_card.yaml 和数据文件。
先验证 design card，然后写一个 analysis plan。
如果是 DID，运行 baseline TWFE、event-study、pre-trend 检查和 placebo 计划。
如果是合成控制，运行 donor pool 审查、pre-fit、placebo-in-space。
所有结果写入 studies/[slug]/outputs，并生成可复现命令。
```
