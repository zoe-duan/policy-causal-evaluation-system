# START HERE

这是一套基于原生 Codex 的因果推断与政策评估工作流。先本地验证，再打开 Codex。

## 1. 本地验证

```bash
python scripts/validate_setup.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/smoke_test.py
```

## 2. 打开 Codex

```bash
codex
```

进入 Codex 后，可以先让它读项目规则：

```text
请阅读 AGENTS.md、.codex/skills 和 knowledge/，然后告诉我这个政策评估系统当前有哪些能力。
```

## 3. 新政策问题入口

```text
我想评估：某城市限行政策是否降低 PM2.5？请先做政策来源搜集、政策文件处理、design card 和方法推荐，不要直接估计。
```

## 4. 一句话继续已有 study

如果已经有 `studies/<slug>`，不要再写长 prompt。直接说：

```text
继续 studies/<slug>，推进到 first-pass estimation。先做 go/no-go 审查；如果缺真实数据，就生成明确标注的 demo data；不要输出真实因果结论。
```

Codex 应使用 `$advance-study-stage`，等价于：

```bash
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data
```

查看状态：

```bash
python scripts/continue_study.py --slug <slug> --status
```

只看调度计划，不写文件：

```bash
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --dry-run
```

## 5. 政策文件处理链路测试

```bash
python scripts/causal_policy_cli.py policy-source-plan \
  --question "某城市限行政策是否降低 PM2.5？"

python scripts/causal_policy_cli.py policy-parse \
  --input examples/policy_documents/sample_transport_restriction_policy.md \
  --evidence-log examples/outputs/policy_evidence_log.csv
```

## 6. 重要边界

- Demo data 只用于测试 workflow，不是真实政策数据。
- First-pass estimation 只是第一版估计，不是最终因果结论。
- 政策事实、数据来源、pre-trends、placebo 和 spillover 检查完成前，不要输出强因果 claim。
