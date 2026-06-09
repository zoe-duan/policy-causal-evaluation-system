# 方法选择示例

| 场景 | 首选方法 | 关键诊断 | 常见失败模式 |
|---|---|---|---|
| 城市 A 推出拥堵收费，其他城市未推出 | DID 或 synthetic control | pre-trend, placebo city/date | 同期交通/环保政策 |
| 一个国家提高最低工资 | synthetic control / comparative interrupted time series | pre-fit, donor pool | donor pool 不可比 |
| 助学金按分数线发放 | RDD | density, covariate continuity | 分数被操纵 |
| 培训名额通过抽签发放 | RCT/IV if noncompliance | balance, first stage | 不遵从、流失 |
| 高维个人数据估计补贴影响 | DML/AIPW | overlap, nuisance performance | 未观测混杂 |
| 想知道哪些家庭最该获得补贴 | causal forest + policy learning | calibration, policy value | 过拟合、忽略公平性 |
