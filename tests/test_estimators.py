from causal_policy_system.estimators import generate_demo_panel, simple_did, twfe_did, partialling_out_dml


def test_demo_estimators_run():
    df = generate_demo_panel(n_cities=10, n_months=20, treated_cities=2, treatment_start=10)
    did = simple_did(df, outcome="pm25", treated="treated_ever", post="post")
    assert did.n_obs == len(df)
    twfe = twfe_did(df, outcome="pm25", treatment="treatment", unit="city", time="month", covariates=["weather_index"], cluster="city")
    assert twfe.standard_error is not None
    dml = partialling_out_dml(df, outcome="pm25", treatment="treatment", covariates=["weather_index", "month"], n_splits=2)
    assert dml.standard_error is not None
