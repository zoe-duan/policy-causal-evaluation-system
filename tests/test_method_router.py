from causal_policy_system.method_router import recommend_methods


def test_panel_policy_routes_to_did():
    recs = recommend_methods("城市-月份面板，政策前后，多个未处理城市，估计限行政策影响")
    assert recs
    assert "DID" in recs[0].method


def test_cutoff_routes_to_rdd():
    recs = recommend_methods("助学金资格由考试分数 cutoff 决定，想估计政策影响")
    assert "RDD" in recs[0].method


def test_heterogeneity_routes_to_forest():
    recs = recommend_methods("谁从培训政策中受益最大？关注异质性和 targeting，有个体协变量")
    methods = " ".join(r.method for r in recs[:2]).lower()
    assert "forest" in methods or "policy" in methods or "因果森林" in methods
