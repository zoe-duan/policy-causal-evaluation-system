# Causal Policy Codex System

一套基于 **原生 Codex** 的因果推断与政策评估工作流。它不是一个普通 Python 包，而是一个可解压即用的 Codex 项目：Codex 打开本仓库后会自动读取 `AGENTS.md`，发现 `.codex/skills` 下的工作流技能，使用 `.codex/agents` 中的专门 subagents，并通过 `.codex/hooks.json` 挂上轻量级质量门禁。

本项目的目标是：当你提出一个政策或事件推测问题，例如“某城市限行政策是否降低了污染？”、“补贴退坡是否影响新能源车销量？”、“平台治理政策是否影响商家进入？”时，Codex 能快速完成：

1. 澄清问题与因果 estimand；
2. 推荐可行识别策略与前沿方法；
3. 搜集和处理政策文件，建立政策事实证据链；
4. 设计数据结构与采集计划；
5. 生成可运行分析脚本；
6. 执行稳健性、安慰剂与威胁审查；
7. 输出研究备忘录、技术报告与复现实验清单。

---

## 1. 最快开始

```bash
unzip causal-policy-codex-system.zip
cd causal-policy-codex-system

git init
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/validate_setup.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/smoke_test.py
python scripts/causal_policy_cli.py recommend --question "某城市限行政策是否降低了 PM2.5？有城市-月份面板数据、政策前后、多个未限行城市。"
```

安装 Codex CLI 后，在仓库根目录运行：

```bash
codex
```

进入 Codex 后可以直接粘贴：

```text
/plan 我想评估“某城市限行政策是否降低了 PM2.5”。请使用本仓库的政策评估工作流，先给出研究设计和方法推荐，不要急着写代码。
```

或显式调用技能：

```text
$policy-evaluation-intake 评估“某城市限行政策是否降低了 PM2.5”，我可能有城市-月份面板数据。
$policy-source-scout 请先给出权威政策来源搜集计划。
$policy-document-processor 请处理 studies/<slug>/policy_documents/raw 下的政策文件，并输出政策时间线、source register 和 treatment 编码建议。
$causal-method-router 请根据上面的 design card 推荐主方法、备选方法、诊断和数据需求。
```

---

## 一句话继续研究：顶层调度器

V2+ 增加了顶层调度器。人不需要再写几百行 prompt，只要给出目标，系统会自动识别当前 study 阶段并调用对应脚本。

在 Codex 里可以直接说：

```text
继续 studies/london-ulez-outer-london-2023，推进到 first-pass estimation。先做 go/no-go 审查；缺真实数据就生成明确标注的 demo data；不要输出真实因果结论。
```

Codex 应使用 `$advance-study-stage`，等价于运行：

```bash
python scripts/continue_study.py \
  --slug london-ulez-outer-london-2023 \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

命令行也可以直接使用：

```bash
python scripts/continue_study.py --slug <study-slug> --status
python scripts/continue_study.py --slug <study-slug> --next-stage auto
python scripts/causal_policy_cli.py continue-study --slug <study-slug> --next-stage first-pass-estimation --demo-if-missing-data
```

调度器会自动写入或更新：

```text
studies/<slug>/study_state.yaml
studies/<slug>/workflow_state.json
studies/<slug>/design_review.md
studies/<slug>/data_sources.md
studies/<slug>/data_readiness_check.md
studies/<slug>/data/processed/analysis_panel.csv    # 仅在允许 demo 或已有真实数据时
studies/<slug>/tables/event_study_results.csv       # first-pass 阶段
studies/<slug>/estimation_report.md
studies/<slug>/orchestrator_summary.md
studies/<slug>/orchestrator_report.md
```

如果缺少 design card 或关键政策事实，调度器会在 `design_review.md` 中显式标出 blocking / non-blocking issues；只有在你明确允许 demo data 时，才会继续做 pipeline 演示，且不会把 demo 输出包装成真实因果结论。


## 2. 本系统怎样使用 Codex 原生能力

| Codex 原生机制 | 本仓库中的实现 | 用途 |
|---|---|---|
| `AGENTS.md` | `AGENTS.md` | 全局工作协议、因果路线图、质量门禁、输出格式 |
| Repository skills | `.codex/skills/*/SKILL.md` | 可复用政策评估工作流，支持显式 `$skill` 调用或自动匹配 |
| Custom subagents | `.codex/agents/*.toml` | 政策来源搜集、政策文件处理、事件侦察、识别审计、方法路由、数据工程、估计、稳健性、政策解释 |
| Project config | `.codex/config.toml` | 子代理并发数、推理强度、沙盒、web search 偏好 |
| Hooks | `.codex/hooks.json` + `.codex/hooks/*.py` | 阻止危险命令、在政策评估/继续研究提示中自动注入路线图和调度器提示 |
| `codex exec` | `prompts/*.md` | 可脚本化批处理，例如自动生成研究设计、审阅报告 |
| 顶层调度器 | `scripts/continue_study.py` + `$advance-study-stage` | 一句话推进已有 study 到设计审查、数据准备和第一版估计 |

---

## 3. 常用工作流

### A. 只有一个想法，先要方法推荐

```bash
python scripts/causal_policy_cli.py recommend \
  --question "补贴退坡是否影响新能源车销量？各省月度销量，有政策前后和对照省份，可能存在异质性。"
```

Codex 版本：

```text
$causal-method-router 补贴退坡是否影响新能源车销量？各省月度销量，有政策前后和对照省份，可能存在异质性。请输出主方法、备选方法、关键假设、诊断、数据需求和风险。
```

### B. 建一个新研究项目

```bash
python scripts/causal_policy_cli.py new-study \
  --slug transport-pollution \
  --question "城市限行政策是否降低 PM2.5？" \
  --event "城市交通限行政策"
```

生成位置：`studies/transport-pollution/`。


### C. 政策文件搜集与处理

先让系统生成搜集计划：

```bash
python scripts/causal_policy_cli.py policy-source-plan \
  --question "某城市限行政策是否降低 PM2.5？"
```

把政策原文、实施细则、地方通知、数据目录等文件放入：

```text
studies/<slug>/policy_documents/raw/
```

然后运行本地抽取：

```bash
python scripts/causal_policy_cli.py process-policy-doc \
  --input studies/<slug>/policy_documents/raw \
  --study-slug <slug>
```

输出包括：

```text
studies/<slug>/policy_documents/source_register.csv
studies/<slug>/policy_documents/processed/policy_document_extraction.json
studies/<slug>/policy_documents/processed/policy_document_summary.md
```

这些文件用于确认政策发布日期、生效日、执行日、适用范围、豁免、处理强度和执法机制。自动抽取只是第一遍，Codex 必须把不确定项标记出来，不能把未核验的政策日期当成事实。

### D. 跑内置 demo

```bash
make demo
```

这会生成一个合成的城市-月份面板数据，完整还原城市限行政策影响 PM2.5 的 demo 链路：raw trends、四格 DID 反事实、TWFE DID、event study、placebo/稳健性检查，并写出：

```text
examples/outputs/demo_report.md
examples/outputs/demo_did_cells.csv
examples/outputs/demo_event_study.csv
examples/outputs/demo_robustness.csv
examples/outputs/figures/*.png
```


### E. 让 Codex 多代理完整评估

复制 `prompts/02_spawn_multi_agent_evaluation.md` 的内容到 Codex，填入你的政策问题。这个 prompt 会明确要求 Codex spawn：

- `policy_source_scout`
- `policy_document_processor`
- `event_scout`
- `identification_auditor`
- `method_router_agent`
- `data_engineer_agent`
- `robustness_reviewer`
- `policy_translator`

Codex 会等子代理结果返回后合并成一个研究方案。


### F. 一句话继续已有研究：顶层调度器

当一个 study 已经有 `studies/<slug>` 目录后，可以直接让 Codex 调用顶层调度器，或在命令行运行：

```bash
python scripts/continue_study.py \
  --slug <study-slug> \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

它会自动识别当前阶段，按需要生成 `design_review.md`、`data_sources.md`、`data_readiness_check.md`、`workflow_state.json`、`orchestrator_summary.md`，并在 first-pass 阶段输出 `estimation_report.md`。

如果没有真实 `analysis_panel.csv`，只有在显式加 `--demo-if-missing-data` 时才会生成明确标注的 DEMO DATA；demo 输出只能用于 workflow 演示，不能当作真实政策结论。

---


## 4. 方法覆盖

本系统内置的路线图覆盖：

- DAG 与识别审查；
- 倾向得分、匹配、分层、回归调整；
- 双重差分、动态 event study、错位实施 DID 风险审查；
- 合成控制、安慰剂和 donor pool 审查；
- 工具变量、2SLS、弱工具变量和排他性约束审查；
- RDD/阈值政策设计；
- Double / Debiased ML、Neyman orthogonality、cross-fitting；
- AIPW / doubly robust learners；
- GRF、因果森林、CATE、policy learning；
- 负向控制、敏感性分析、伪政策、伪结果、随机化推断；
- 政策文件来源搜集、原文抽取、政策时间线、source register；
- 政策解释、外推限制、伦理和公平性审查。

---

## 5. 重要边界

这个系统可以帮你快速形成研究设计和可执行分析，但不会替代识别假设本身。Codex 必须在报告中明确区分：

- 已识别的因果效应；
- 仅相关的描述性结果；
- 需要额外数据或制度背景才能判断的假设；
- 对政策制定的可转化建议。

任何真实政策评估都需要你核验制度细节、数据口径、样本选择、政策执行时间和潜在溢出效应。

---

## 6. 目录结构

```text
AGENTS.md                         # Codex 自动读取的项目工作协议
.codex/config.toml                # Codex 项目配置
.codex/agents/*.toml              # 专门 subagents
.codex/hooks.json                 # Hooks 配置
.codex/skills/*/SKILL.md          # Codex 原生 skills
knowledge/                        # 方法知识库、政策来源库、政策文件处理协议
templates/                        # Design card、报告、数据字典模板
prompts/                          # 可复制到 Codex 的任务入口
src/causal_policy_system/         # 轻量 Python helper 包
scripts/                          # CLI、demo、校验脚本
examples/                         # 示例问题、示例 design card、demo 数据
studies/                          # 你的真实研究项目生成位置
R/                                # R/grf/DoubleML 模板
```

---

## 7. 推荐第一条 Codex prompt

```text
我正在使用这个仓库建立“因果推断与政策评估系统”。请先阅读 AGENTS.md、knowledge/causal_roadmap.md、knowledge/method_matrix.md、.codex/skills 下的技能说明。然后进入 plan mode，检查系统是否准备好，最后用 examples/policy_questions/urban_transport_pollution.md 跑一个端到端演示，不要删除任何文件。
```
