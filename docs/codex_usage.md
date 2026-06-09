# Codex 使用方式

## 初始化

```bash
unzip causal-policy-codex-system.zip
cd causal-policy-codex-system
git init
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_setup.py
codex
```

进入 Codex 后建议第一句：

```text
请先阅读 AGENTS.md、START_HERE.md 和 knowledge/method_playbook.md，然后告诉我这个系统如何处理一个新的政策评估问题。
```

## 常用 Codex 命令

- `/plan`：先规划研究路径，再动手。
- `/skills`：检查 Codex 识别到的 skills。
- `/agent`：调用项目内自定义 agents。
- `/review`：让 Codex 进行审查式 review。

## 常用本地命令

```bash
python scripts/causal_policy_cli.py recommend --question "某城市限行政策是否降低 PM2.5？有城市-月份面板数据。"
python scripts/causal_policy_cli.py new-study --slug traffic-pm25 --question "某城市限行政策是否降低 PM2.5？"
python scripts/causal_policy_cli.py validate-card studies/traffic-pm25/design_card.yaml --recommend
python scripts/run_demo_analysis.py
```

## 重要边界

Codex 可以快速生成研究设计、脚本和审查清单，但不能替代数据质量审计、制度背景验证、伦理审查和领域专家判断。任何政策建议都必须明确“可识别的因果效应”和“政策价值判断”之间的区别。
