# Continue an existing study

Use this when you want Codex to advance an existing study without a long prompt.

```text
继续 studies/<slug> 这个研究，推进到 first-pass estimation。先做 go/no-go 审查；如果缺真实数据，就生成明确标注的 demo data；不要输出真实因果结论。
```

The intended tool path is:

```bash
python scripts/continue_study.py --slug <slug> --next-stage first-pass-estimation --demo-if-missing-data
```
