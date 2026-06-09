# 顶层调度器：Study Orchestrator

这个仓库现在支持一句话推进研究阶段，不再需要手写很长的 prompt。

## 最短用法

```bash
python scripts/continue_study.py \
  --slug london-ulez-outer-london-2023 \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

或者通过主 CLI：

```bash
python scripts/causal_policy_cli.py continue-study \
  --slug london-ulez-outer-london-2023 \
  --next-stage first-pass-estimation \
  --demo-if-missing-data
```

## 在 Codex 里怎么说

只需要说：

```text
继续 ULEZ demo，推进到 first-pass estimation。缺真实数据就用明确标注的 demo data，不要输出真实因果结论。
```

Codex 会通过 `$advance-study-stage` skill 和 `scripts/continue_study.py` 自动展开流程。

## 它会自动做什么

`continue_study.py` 会：

1. 识别 `studies/<slug>` 当前阶段；
2. 生成或更新 `design_review.md`；
3. 准备数据目录；
4. 生成 `data_sources.md` 和 `data_readiness_check.md`；
5. 如果缺真实 `analysis_panel.csv` 且允许 demo，则生成明确标注的 demo panel；
6. 运行第一版 event-study；
7. 输出 `estimation_report.md`、图表和表格；
8. 写入 `orchestrator_summary.md`。

## 阶段识别

| 阶段 | 判定依据 |
|---|---|
| `empty` | 研究目录存在但缺主要产物，或还没有创建实际 study |
| `policy_facts` | 有政策来源登记、政策文件抽取或政策摘要 |
| `design_only` | `design_card.yaml` 已存在 |
| `data_prepared` | `data_sources.md` 或 `data_readiness_check.md` 已存在 |
| `panel_ready` | `data/processed/analysis_panel.csv` 存在且非空 |
| `first_pass_estimated` | 有 `estimation_report.md` 和 event-study 表 |
| `robustness_reviewed` | 有 `robustness_plan.md` 或 `robustness_review.md` |

## 常用命令

查看状态：

```bash
python scripts/continue_study.py --slug <slug> --next-stage status
```

只做 dry run：

```bash
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --dry-run
```

进入数据阶段：

```bash
python scripts/continue_study.py --slug <slug> --next-stage data-prep
```

第一版估计，真实数据缺失时允许 demo：

```bash
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data
```

## 重要边界

- Demo data 只用于验证工作流、图表和估计脚本。
- Demo data 不能作为真实政策结论。
- 如果 design review 失败，系统不会把结果包装成正式因果结论。
- `data/raw` 和用户提供文件不能被覆盖。
