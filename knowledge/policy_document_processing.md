# 政策文件处理规范

政策评估的核心输入不是“政策听说发生了”，而是可审计、可复现的政策原文和编码规则。

## 1. 文件类型

常见文件包括：法律条文、行政法规、部门规章、地方通知、预算文件、试点名单、处罚/执法公告、平台规则、FAQ、新闻发布会问答、统计口径说明、数据字典。

## 2. 原始文件保存

- 原始文件放在 `studies/<slug>/policy_documents/raw/` 或 `studies/<slug>/policy_documents/`；
- 不直接修改 raw 文件；
- 每个文件记录 SHA256；
- 对网页同时保存 HTML/raw bytes 和抽取文本；
- 对 PDF 尽量保存原 PDF，OCR 或文本抽取结果作为派生文件。

## 3. 结构化抽取字段

每个政策文件至少抽取：

```yaml
source_id:
title:
source_type:
source_url:
local_path:
content_sha256:
captured_at:
authority_score:
issuing_agency:
jurisdiction:
publication_date:
effective_date:
policy_action:
target_population:
treatment_definition:
treatment_intensity:
outcomes_mentioned:
timeline:
key_quotes:
extraction_warnings:
```

## 4. 处理命令

解析本地文件：

```bash
python scripts/causal_policy_cli.py policy-parse \
  --input examples/policy_documents/sample_transport_restriction_policy.md \
  --evidence-log examples/outputs/policy_evidence_log.csv
```

抓取 URL 并解析：

```bash
python scripts/causal_policy_cli.py policy-fetch \
  --url "https://official.example/path/to/policy" \
  --out-dir studies/<slug>/policy_documents/raw \
  --parse
```

当前环境无法联网时，Codex 应输出搜索计划、字段清单和待核验来源，不得编造政策事实。

## 5. 从文本到 treatment coding

Codex 必须把文本转换成可估计变量：

- binary treatment: 是否受政策覆盖；
- event_time: 相对生效日期的月份/季度；
- dose/intensity: 补贴金额、税率、限制强度、执法频次；
- eligibility: 阈值、名单、行业、地区、年龄、收入、规模；
- exposure: 空间半径、平台曝光、供应链或网络接触；
- exceptions: 豁免、过渡期、执行延期。

## 6. 人工复核点

自动抽取永远不是最终证据。报告前必须人工复核：

- 日期是否是发布日期还是生效日期；
- 政策覆盖是否包含试点/例外；
- 是否存在修订、延期、废止；
- 政策执行是否实际落地；
- 文件是否来自权威原始来源；
- 编码规则是否会造成 post-treatment control 或样本选择偏误。
