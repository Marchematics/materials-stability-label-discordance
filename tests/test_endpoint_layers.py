from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "repaired_model_evaluation_v2"


def test_endpoint_layers_keep_audit_policy_separate() -> None:
    definitions = pd.read_csv(OUT / "endpoint_definition_table.csv").set_index("endpoint")
    assert definitions.loc["audit_view", "layer"] == "audit_policy"
    assert definitions.loc["consensus", "layer"] == "selection_policy"
    assert int(definitions.loc["common_pool", "support_n"]) == 31_872


def test_hull_construction_band_excludes_audit_policy() -> None:
    bands = pd.read_csv(OUT / "band_and_model_spread_fixed_support.csv")
    primary = bands[bands.scope.eq("hull_construction_sensitivity")]
    assert set(primary.n_views.dropna().astype(int)) == {4}
    assert not primary["scope"].astype(str).str.contains("audit").any()


def test_bootstrap_ratio_recomputes_numerator_and_denominator() -> None:
    ratios = pd.read_csv(OUT / "endpoint_sensitivity_to_model_spread_ratio_bootstrap.csv")
    primary = ratios[
        ratios.scope.eq("hull_construction_sensitivity")
        & ratios.metric.isin(["f1_fixed_threshold", "auprc", "stable_yield_at_1000"])
    ]
    assert len(primary) == 12
    assert (primary.ratio_ci_low_95 > 1).all()
