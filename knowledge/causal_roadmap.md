# Causal Roadmap for Policy Evaluation

## 0. Do not start with the estimator

The estimator is not the design. Always define:

- **Policy/event**: what changed, where, when, and for whom?
- **Counterfactual**: what would have happened without the policy?
- **Estimand**: ATE, ATT, CATE, LATE, dynamic ATT, policy value, spillover effect.
- **Assignment mechanism**: why some units were treated and others not.

## 1. Question template

```text
For population P, units U, time window T, what is the causal effect of policy/intervention D on outcome Y, relative to counterfactual C?
```

## 2. Design card minimum fields

- `question`
- `policy_event`
- `unit_of_analysis`
- `treatment`
- `outcomes`
- `estimand`
- `identification_strategy`
- `data_requirements`
- `diagnostics`
- `robustness_checks`
- `threats_to_validity`
- `deliverables`

## 3. Identification checklist

- Are treated and control units comparable before treatment?
- Is treatment timing plausibly exogenous after controls/design?
- Are there anticipation effects?
- Are there spillovers or interference?
- Is outcome measurement stable across treated/control groups?
- Are controls pre-treatment, not mediators or colliders?
- Is sample selection affected by treatment?
- Are standard errors clustered at the policy assignment level?
- Is there enough pre-period information?
- Is external validity limited to treated units or broader population?

## 4. Evidence strength labels

- **Strong**: credible quasi-random or randomized assignment, passed core diagnostics, robust across designs.
- **Moderate**: plausible design with some untestable assumptions and good falsification checks.
- **Weak**: identification depends heavily on unverified assumptions or fragile diagnostics.
- **Design-only**: data or assignment is not sufficient for causal effect estimation yet.

## 5. Reporting discipline

Never write “the policy caused X” unless the report states the identifying assumptions. Prefer:

> Under the maintained DID assumptions, the estimated ATT is...

or

> This is descriptive and should not be interpreted causally because...
