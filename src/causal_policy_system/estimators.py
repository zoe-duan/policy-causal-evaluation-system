from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd


@dataclass
class EstimateResult:
    method: str
    estimate: float
    standard_error: float | None
    n_obs: int
    details: dict[str, float | int | str]

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "n_obs": self.n_obs,
            "details": self.details,
        }


def load_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def simple_did(
    df: pd.DataFrame,
    *,
    outcome: str,
    treated: str,
    post: str,
) -> EstimateResult:
    """Four-cell DID estimator for a binary treated-by-post design."""
    required = [outcome, treated, post]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    sub = df[required].dropna().copy()
    sub[treated] = sub[treated].astype(int)
    sub[post] = sub[post].astype(int)
    cells = sub.groupby([treated, post])[outcome].mean()
    try:
        y11 = cells.loc[(1, 1)]
        y10 = cells.loc[(1, 0)]
        y01 = cells.loc[(0, 1)]
        y00 = cells.loc[(0, 0)]
    except KeyError as exc:
        raise ValueError("DID needs all four treated/post cells.") from exc
    est = (y11 - y10) - (y01 - y00)
    return EstimateResult(
        method="simple four-cell DID",
        estimate=float(est),
        standard_error=None,
        n_obs=int(len(sub)),
        details={"treated_post": float(y11), "treated_pre": float(y10), "control_post": float(y01), "control_pre": float(y00)},
    )


def twfe_did(
    df: pd.DataFrame,
    *,
    outcome: str,
    treatment: str,
    unit: str,
    time: str,
    covariates: Iterable[str] | None = None,
    cluster: str | None = None,
) -> EstimateResult:
    """Two-way fixed-effect DID using statsmodels.

    This is a baseline estimator. For staggered timing and heterogeneous effects,
    use this only as a benchmark and prefer group-time ATT/event-study estimators.
    """
    import statsmodels.formula.api as smf

    covariates = list(covariates or [])
    required = [outcome, treatment, unit, time, *covariates]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    data = df[required].dropna().copy()
    formula = f"{outcome} ~ {treatment} + C({unit}) + C({time})"
    if covariates:
        formula += " + " + " + ".join(covariates)
    model = smf.ols(formula, data=data)
    if cluster and cluster in data.columns:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster]})
    elif cluster == unit:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": data[unit]})
    else:
        fit = model.fit(cov_type="HC1")
    return EstimateResult(
        method="TWFE DID baseline",
        estimate=float(fit.params[treatment]),
        standard_error=float(fit.bse[treatment]),
        n_obs=int(fit.nobs),
        details={"r_squared": float(fit.rsquared), "formula": formula},
    )


def event_study_coefficients(
    df: pd.DataFrame,
    *,
    outcome: str,
    event_time: str,
    unit: str,
    time: str,
    treated_ever: str,
    omit_event_time: int = -1,
    window: tuple[int, int] = (-5, 5),
) -> pd.DataFrame:
    """Baseline event-study with unit and time fixed effects.

    Returns coefficients for treated units by event time. The omitted period is
    `omit_event_time`. For production, prefer specialized staggered-DID packages.
    """
    import statsmodels.formula.api as smf

    low, high = window
    data = df[[outcome, event_time, unit, time, treated_ever]].dropna().copy()
    data = data[(data[event_time] >= low) & (data[event_time] <= high)].copy()
    terms: list[str] = []
    created: list[str] = []
    for k in range(low, high + 1):
        if k == omit_event_time:
            continue
        sign = "m" if k < 0 else "p"
        col = f"event_{sign}{abs(k)}"
        data[col] = ((data[event_time] == k) & (data[treated_ever].astype(bool))).astype(int)
        terms.append(col)
        created.append(col)
    formula = f"{outcome} ~ {' + '.join(terms)} + C({unit}) + C({time})"
    fit = smf.ols(formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": data[unit]})
    rows = []
    for k, col in zip([x for x in range(low, high + 1) if x != omit_event_time], created):
        rows.append({"event_time": k, "estimate": fit.params.get(col, np.nan), "standard_error": fit.bse.get(col, np.nan)})
    return pd.DataFrame(rows)


def synthetic_control_weights(
    pre_treated: np.ndarray,
    pre_donors: np.ndarray,
) -> np.ndarray:
    """Non-negative least squares weights normalized to sum to one."""
    from scipy.optimize import nnls

    pre_treated = np.asarray(pre_treated, dtype=float)
    pre_donors = np.asarray(pre_donors, dtype=float)
    if pre_donors.ndim != 2:
        raise ValueError("pre_donors must be a 2D array shaped periods x donors")
    weights, _ = nnls(pre_donors, pre_treated)
    if weights.sum() <= 0:
        weights = np.ones(pre_donors.shape[1]) / pre_donors.shape[1]
    else:
        weights = weights / weights.sum()
    return weights


def partialling_out_dml(
    df: pd.DataFrame,
    *,
    outcome: str,
    treatment: str,
    covariates: list[str],
    n_splits: int = 3,
    random_state: int = 123,
) -> EstimateResult:
    """Minimal partialling-out DML for a continuous/binary treatment.

    This compact implementation is for templates and smoke tests. For research
    use, compare with DoubleML/EconML and document learner choices.
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import KFold
    import statsmodels.api as sm

    data = df[[outcome, treatment, *covariates]].dropna().copy()
    y = data[outcome].to_numpy(dtype=float)
    d = data[treatment].to_numpy(dtype=float)
    x = data[covariates].to_numpy(dtype=float)
    y_res = np.empty_like(y)
    d_res = np.empty_like(d)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    for train_idx, test_idx in kf.split(x):
        y_model = RandomForestRegressor(n_estimators=20, min_samples_leaf=5, random_state=random_state)
        d_model = RandomForestRegressor(n_estimators=20, min_samples_leaf=5, random_state=random_state + 1)
        y_model.fit(x[train_idx], y[train_idx])
        d_model.fit(x[train_idx], d[train_idx])
        y_res[test_idx] = y[test_idx] - y_model.predict(x[test_idx])
        d_res[test_idx] = d[test_idx] - d_model.predict(x[test_idx])
    fit = sm.OLS(y_res, sm.add_constant(d_res)).fit(cov_type="HC1")
    return EstimateResult(
        method="partialling-out DML template",
        estimate=float(fit.params[1]),
        standard_error=float(fit.bse[1]),
        n_obs=int(len(data)),
        details={"n_splits": n_splits, "learner": "RandomForestRegressor(n_estimators=20)"},
    )


def generate_demo_panel(
    *,
    n_cities: int = 24,
    n_months: int = 36,
    treated_cities: int = 6,
    treatment_start: int = 20,
    effect: float = -2.0,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    city_ids = [f"city_{i:02d}" for i in range(n_cities)]
    treated_set = set(city_ids[:treated_cities])
    rows = []
    city_fe = rng.normal(0, 3, n_cities)
    for i, city in enumerate(city_ids):
        for month in range(n_months):
            treated_ever = int(city in treated_set)
            post = int(month >= treatment_start)
            treatment = treated_ever * post
            weather = rng.normal(0, 1)
            trend = 0.10 * month
            seasonal = 1.5 * np.sin(month / 12 * 2 * np.pi)
            y = 35 + city_fe[i] + trend + seasonal + 0.7 * weather + effect * treatment + rng.normal(0, 1.5)
            rows.append(
                {
                    "city": city,
                    "month": month,
                    "treated_ever": treated_ever,
                    "post": post,
                    "treatment": treatment,
                    "event_time": month - treatment_start if treated_ever else -999,
                    "weather_index": weather,
                    "pm25": y,
                }
            )
    return pd.DataFrame(rows)
