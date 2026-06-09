# 示例：城市交通限行政策对 PM2.5 的影响

## 1. 政策问题
某城市交通限行政策是否降低 PM2.5？我们有城市-月份面板数据、政策前后、多个未限行城市。

## 2. 推荐识别策略

## 1. 双重差分 DID / event-study / staggered adoption
**为什么**：适合政策前后、处理组与对照组、面板或重复截面数据的问题。 路由得分=11。
**需要的数据**：单位 ID；时间 ID；处理开始时间；结果变量；处理前后协变量；潜在对照组
**识别假设**：平行趋势；无预期效应或可建模；无严重溢出；构成变化可控；处理时间记录准确
**估计器**：两维固定效应 TWFE；Sun-Abraham / Callaway-Sant'Anna 风格分组时间 ATT；事件研究；聚类稳健标准误
**诊断**：处理前趋势图；placebo leads；事件时间系数；平衡性和样本构成检查；不同对照组敏感性
**失败模式**：处理效应异质且 staggered TWFE 权重异常；政策前已有趋势差异；同时发生的政策冲击；跨地区溢出
**下一步**：先画 raw trends；定义 never-treated 或 not-yet-treated 对照组；写明处理日期和事件窗口；规划 placebo 与 alternative controls


## 3. 基线估计结果

- **simple four-cell DID**：估计值 `-1.7094`，标准误 `NA`，样本量 `864`。
  - details: treated_post=34.32135399050137; treated_pre=34.98419526515814; control_post=37.53643893248996; control_pre=36.48989227809412
- **TWFE DID baseline**：估计值 `-1.7653`，标准误 `0.1945`，样本量 `864`。
  - details: r_squared=0.814209258343567; formula=pm25 ~ treatment + C(city) + C(month) + weather_index

## 4. 必做稳健性与敏感性

- 识别假设反驳表：逐条列出最可能破坏识别的机制。
- 替代样本、替代对照组、替代结果变量。
- placebo timing / placebo units。
- 预趋势或断点/工具变量/重叠等设计特定诊断。
- 把统计显著性、效应大小、政策成本和可执行性分开报告。

## 5. 局限

- 这是合成数据，仅用于验证系统可运行。
- 真实研究需要处理政策选择、污染物监测口径、气象冲击、相邻城市溢出和工业结构变化。
- staggered adoption 时不应只依赖 TWFE；需使用分组-时间 ATT 或稳健事件研究。

## 6. Codex 复现提示

在 Codex 中继续分析时，建议执行：

```text
/skills
使用 causal-method-router、did-event-study、robustness-sensitivity、replication-report 四个 skills。
请先生成 design card，再运行 baseline estimator，最后让 robustness_reviewer subagent 审查识别假设。
```
