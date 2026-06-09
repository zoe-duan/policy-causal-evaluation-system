# Prompt 03 — 方法推荐

```text
请使用 $causal-method-router，并结合 knowledge/method_matrix.md 和已核验的政策来源记录。
对这个问题推荐 3-5 个候选方法，按优先级排序。
每个方法必须说明：为什么适合、需要什么数据、识别假设、诊断、失败模式、最小可运行估计器。
请同时运行：python scripts/causal_policy_cli.py recommend --question "[问题]"
把脚本输出和你的实质判断合并。
如果政策日期、覆盖范围或处理强度未核验，请先回到 $policy-source-scout / $policy-document-processor，不要假设这些事实。
```
