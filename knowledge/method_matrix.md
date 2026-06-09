# Method Matrix

| Method | Best when | Key assumptions | Diagnostics | Outputs | Common failure modes |
|---|---|---|---|---|---|
| RCT / A/B / randomized rollout | Treatment assigned randomly | Randomization valid, attrition unrelated, SUTVA | Balance, attrition, compliance | ATE/ITT/TOT | Noncompliance, interference, attrition |
| Matching / PSM / stratification | Treatment selection observed in rich pre-treatment covariates | Conditional ignorability, overlap | Balance, propensity overlap, sensitivity | ATT/ATE | Unobserved confounding, bad matches |
| Regression adjustment | Rich covariates, functional form credible | No omitted confounders, correct adjustment set | Residuals, overlap, model sensitivity | Conditional mean effects | Bad controls, post-treatment controls |
| DID | Treated/control units before and after policy | Parallel trends, no anticipation, stable composition | Pre-trends, placebo outcomes, event study | ATT, dynamic effects | Staggered timing bias, spillovers, shocks |
| Event study | Need dynamic effects around event | Parallel pre-trends, valid comparison, correct timing | Leads near zero, lag pattern, window sensitivity | Dynamic ATT | Multiple testing, anticipation |
| Synthetic control | One/few treated aggregate units and donor pool | Donor pool can reconstruct counterfactual, no contamination | Pre-fit RMSPE, placebo units, donor weights | Unit-level ATT path | Poor pre-fit, extrapolation, donor contamination |
| Synthetic DID / matrix completion | Panel data with treated/control and low-rank structure | Latent factor structure, enough pre-periods | Placebo, matrix fit, window sensitivity | ATT | Weak overlap in latent factors |
| IV / 2SLS | Valid instrument shifts treatment | Relevance, exclusion, independence, monotonicity | First stage, weak IV, over-ID if possible | LATE | Invalid exclusion, weak instrument |
| RDD | Treatment changes at cutoff | Continuity around cutoff, no manipulation | Density test, covariate balance, bandwidth sensitivity | Local ATE | Sorting/manipulation, wrong bandwidth |
| DML / Double ML | High-dimensional controls, target ATE/ATT with observed confounding | Conditional ignorability, overlap, orthogonal score | Cross-fitting, nuisance performance, overlap | ATE/ATT with robust nuisance ML | ML cannot fix unobserved confounding |
| AIPW / DR learner | Need doubly robust ATE/CATE with covariates | Either outcome or propensity model correct, overlap | Overlap, nuisance diagnostics | ATE/CATE | Extreme weights, model misspecification |
| Causal forest / GRF | Need heterogeneous treatment effects | Identification for treatment assignment, overlap, honest splitting | CATE calibration, subgroup stability | CATE, best linear projection | Fishing heterogeneity, weak overlap |
| Policy learning | Need treatment targeting rule | Valid CATE estimates, welfare objective specified | Out-of-sample policy value, regret, fairness | Policy rule/value | Optimizing noise, unfair targeting |
| Negative controls | Need falsification of hidden bias | Negative outcome/exposure truly unaffected | Significant negative-control effects indicate bias | Bias evidence | Invalid negative control |

## Routing priority

1. Prefer design-based identification over flexible ML.
2. Use ML to improve nuisance estimation or heterogeneity only after identifying assumptions are credible.
3. Always pair main estimator with diagnostics and falsification checks.
4. Report “not enough design information” rather than forcing a method.
