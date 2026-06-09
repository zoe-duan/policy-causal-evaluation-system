# Continue an existing study with the top-level orchestrator

Copy one of these into Codex.

```text
继续 <study-slug> 这个研究，推进到下一阶段。请使用 $advance-study-stage 和 scripts/continue_study.py 自动调度，不要让我写长 prompt。
```

For first-pass estimation with demo data allowed only when real data are missing:

```text
继续 <study-slug>，推进到 first-pass estimation。先做 go/no-go 审查；如果缺真实数据，就使用明确标注的 demo data；不要输出真实因果结论。
```

For the ULEZ demo:

```text
继续 ULEZ demo，推进到 first-pass estimation。先做 go/no-go 审查；如果缺真实数据，就使用明确标注的 demo data；不要输出真实因果结论。
```
