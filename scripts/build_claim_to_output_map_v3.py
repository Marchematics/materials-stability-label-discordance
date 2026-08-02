#!/usr/bin/env python3
"""Lock every planned abstract/result number to one machine-readable output."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"
EVAL = OUT / "evaluation"


def row(
    claim_id: str,
    claim_scope: str,
    quantity: str,
    value,
    unit: str,
    denominator: str,
    source_file: Path,
    selector: str,
    source_column: str,
    interpretation: str,
) -> dict:
    return {
        "claim_id": claim_id,
        "claim_scope": claim_scope,
        "quantity": quantity,
        "value": value,
        "unit": unit,
        "denominator": denominator,
        "source_file": str(source_file.relative_to(ROOT)),
        "selector": selector,
        "source_column": source_column,
        "interpretation": interpretation,
        "lock_status": "locked_to_unique_machine_readable_source",
    }


def main() -> None:
    rows = []
    flow_path = EVAL / "physical_support_flow.csv"
    flow = pd.read_csv(flow_path)
    mphys = flow[flow.stage.eq("Mphys fixed physical evaluation support")].iloc[0]
    rows.append(
        row(
            "A1_MPHYS_SUPPORT", "abstract", "five_physical_endpoint_common_support_n",
            int(mphys.n), "rows", "frozen matched compound candidates",
            flow_path, 'stage == "Mphys fixed physical evaluation support"', "n",
            "Common support is formed only after rankings and coordinates are frozen.",
        )
    )

    threshold_path = EVAL / "endpoint_threshold_scan.csv"
    threshold = pd.read_csv(threshold_path)
    for threshold_mev in (0, 50):
        subset = threshold[
            threshold.support.eq("D2_native_full")
            & threshold.threshold_meV_per_atom.eq(threshold_mev)
        ]
        for bound, value in (("minimum", subset.switch_rate.min()), ("maximum", subset.switch_rate.max())):
            rows.append(
                row(
                    f"A2_NATIVE_SWITCH_T{threshold_mev}_{bound.upper()}", "abstract",
                    f"{bound}_native_pair_switch_rate_at_{threshold_mev}_meV",
                    float(value), "fraction", "D2 native full support (n=36,802)",
                    threshold_path,
                    f'support == "D2_native_full" and threshold_meV_per_atom == {threshold_mev}',
                    "switch_rate",
                    "Range across the three native-coordinate source pairs.",
                )
            )

    ind_path = EVAL / "indeterminate_zone_conflicts.csv"
    ind = pd.read_csv(ind_path)
    robust = ind[
        ind.support.eq("D2_reconstructable")
        & ind.indeterminate_width_meV_per_atom.eq(50)
        & ind.endpoint_a.eq("mp_source_coordinate")
        & ind.endpoint_b.eq("alex_pbe_source_coordinate")
    ].iloc[0]
    selector = (
        'support == "D2_reconstructable" and indeterminate_width_meV_per_atom == 50 '
        'and endpoint_a == "mp_source_coordinate" and endpoint_b == "alex_pbe_source_coordinate"'
    )
    for suffix, column, unit, denominator in (
        ("COUNT", "robust_conflict_n", "rows", "36,770 reconstructable rows"),
        ("FULL_RATE", "robust_conflict_rate_full_support", "fraction", "36,770 reconstructable rows"),
        ("DECISIVE_RATE", "robust_conflict_rate_decisive_support", "fraction", "decisive rows only"),
    ):
        rows.append(
            row(
                f"A3_ROBUST_CONFLICT_{suffix}", "abstract", column,
                int(robust[column]) if column.endswith("_n") else float(robust[column]),
                unit, denominator, ind_path, selector, column,
                "Definite stable-versus-definite unstable MP--Alexandria-PBE conflict.",
            )
        )

    winner_path = OUT / "bootstrap" / "model_winner_frequencies_cluster_bootstrap.csv"
    winner = pd.read_csv(winner_path)
    mace = winner[
        winner.threshold_meV_per_atom.eq(0)
        & winner.metric.isin(["auroc", "ap", "normalized_ap"])
        & winner.model_name.eq("MACE-MP")
    ]
    rows.append(
        row(
            "A4_GLOBAL_MACE_WINNER_MIN_FREQUENCY", "abstract",
            "minimum_MACE_MP_bootstrap_winner_frequency_across_global_metrics_and_endpoints",
            float(mace.winner_frequency.min()), "fraction", "15 endpoint-metric combinations",
            winner_path,
            'threshold_meV_per_atom == 0 and metric in {"auroc","ap","normalized_ap"} and model_name == "MACE-MP"',
            "winner_frequency", "Chemical-system bootstrap conditional on fixed predictions and pools.",
        )
    )

    budget_path = EVAL / "budget_sensitivity_audit.csv"
    budget = pd.read_csv(budget_path)
    point = budget[
        budget.threshold_meV_per_atom.eq(0) & budget.K.eq(1000) & budget.point_winner
    ]
    rows.append(
        row(
            "A5_TOP1000_POINT_WINNER_SET", "abstract", "point_winner_models_across_endpoints",
            json.dumps(sorted(point.model_name.unique())), "model names", "five physical endpoints",
            budget_path,
            "threshold_meV_per_atom == 0 and K == 1000 and point_winner == True",
            "model_name", "Point-estimate winners vary across endpoints; this is not a probability claim.",
        )
    )

    regret_path = OUT / "bootstrap" / "endpoint_selection_regret_cluster_bootstrap.csv"
    regret = pd.read_csv(regret_path)
    regret = regret[
        regret.threshold_meV_per_atom.eq(0)
        & regret.metric.eq("expected_stable_hits_at_1000")
        & ~regret.coordinate_endpoint.eq("mp_source_coordinate")
    ]
    for bound, value in (("minimum", regret.regret_max_median.min()), ("maximum", regret.regret_max_median.max())):
        rows.append(
            row(
                f"A6_MP_SELECTION_REGRET_MEDIAN_{bound.upper()}", "abstract",
                f"{bound}_median_MP_selection_regret_across_non_MP_endpoints",
                float(value), "stable hits per 1000", "four non-MP physical endpoints",
                regret_path,
                'threshold_meV_per_atom == 0 and metric == "expected_stable_hits_at_1000" and coordinate_endpoint != "mp_source_coordinate"',
                "regret_max_median", "Regret is endpoint best minus an MP-selected model within each bootstrap replicate.",
            )
        )

    old_path = OUT / "superseded_ranking_audit" / "previous_self_included_hull_tie_audit.csv"
    old = pd.read_csv(old_path)
    old1000 = old[old.K.eq(1000)]
    for bound, value in (("minimum", old1000.boundary_tie_n.min()), ("maximum", old1000.boundary_tie_n.max())):
        rows.append(
            row(
                f"R1_WITHDRAWN_TIE_{bound.upper()}", "reviewer_response",
                f"{bound}_withdrawn_top1000_boundary_tie_size", int(value), "rows",
                "four previous self-included model rankings", old_path, "K == 1000",
                "boundary_tie_n", "Superseded analysis; retained only as a failure audit.",
            )
        )

    old_compare_path = OUT / "superseded_ranking_audit" / "previous_row_id_vs_analytic_tie_topk.csv"
    old_compare = pd.read_csv(old_compare_path)
    mace_old = old_compare[
        old_compare.model_name.eq("MACE-MP")
        & old_compare.endpoint.eq("mp_native")
        & old_compare.K.eq(1000)
    ].iloc[0]
    for claim_id, column, unit in (
        ("R2_OLD_MACE_ROW_ID_HITS", "row_id_selected_hits", "stable hits"),
        ("R3_OLD_MACE_TIE_EXPECTATION", "expected_stable_hits", "stable hits"),
        ("R4_OLD_MACE_TIE_CI_LOW", "tie_interval_low_hits", "stable hits"),
        ("R5_OLD_MACE_TIE_CI_HIGH", "tie_interval_high_hits", "stable hits"),
    ):
        rows.append(
            row(
                claim_id, "reviewer_response", column, float(mace_old[column]), unit,
                "previous MACE-MP MP-native top-1000",
                old_compare_path, 'model_name == "MACE-MP" and endpoint == "mp_native" and K == 1000',
                column, "Superseded analysis diagnostic.",
            )
        )

    exclusion_path = OUT / "loso_exclusion_audit_summary.csv"
    exclusion = pd.read_csv(exclusion_path)
    primary_exclusion = exclusion[exclusion.setting.eq("primary")]
    rows.append(
        row(
            "R6_PRIMARY_EXCLUSION_EVALUATION_N", "reviewer_response",
            "primary_candidate_model_exclusion_evaluation_n",
            int(primary_exclusion.row_n.sum()), "candidate-model evaluations",
            "four primary rankings over 36,681 compound candidates", exclusion_path,
            'setting == "primary"', "row_n",
            "Each row records full equivalence-class and decomposition-simplex exclusion.",
        )
    )
    rows.append(
        row(
            "R6_PRIMARY_SIMPLEX_OVERLAP_N", "reviewer_response",
            "excluded_equivalence_class_rows_in_decomposition_simplex_n",
            int(primary_exclusion.simplex_overlap_n.sum()), "failed evaluations",
            "146,724 primary candidate-model evaluations", exclusion_path,
            'setting == "primary"', "simplex_overlap_n",
            "Zero means no excluded equivalence-class row appears in any decomposition simplex.",
        )
    )

    common_path = EVAL / "common_pool_decomposition_threshold_scan.csv"
    common = pd.read_csv(common_path)
    common0 = common[common.support.eq("D2") & common.threshold_meV_per_atom.eq(0)].iloc[0]
    for column in (
        "all_native_conflict_n", "reconstructable_native_conflict_n",
        "unreconstructable_native_conflict_n", "phase_pool_sensitive_n",
        "persistent_conflict_n", "hidden_common_pool_conflict_n", "common_pool_conflict_n",
    ):
        rows.append(
            row(
                f"R6_COMMON_{column.upper()}", "results", column, int(common0[column]), "rows",
                "D2; reconstructable subset where required", common_path,
                'support == "D2" and threshold_meV_per_atom == 0', column,
                "Operational conflict component with explicit denominator.",
            )
        )

    mphys_audit_path = OUT / "mphys_support_exclusion_audit" / "mphys_retained_excluded_summary.csv"
    mphys_audit = pd.read_csv(mphys_audit_path)
    mphys_meta_path = OUT / "mphys_support_exclusion_audit" / "mphys_retained_excluded_metadata.json"
    mphys_meta = json.loads(mphys_meta_path.read_text())
    for claim_id, quantity, value, denominator, source_file, selector, source_column, interpretation in (
        (
            "R7_MPHYS_RETAINED_N", "Mphys_retained_n", int(mphys_meta["mphys_retained_n"]),
            "frozen compound candidate universe", mphys_meta_path, "top-level metadata", "mphys_retained_n",
            "Rows with all four rankings and all five physical hull coordinates.",
        ),
        (
            "R8_MPHYS_EXCLUDED_N", "candidate_excluded_from_Mphys_n", int(mphys_meta["candidate_excluded_n"]),
            "frozen compound candidate universe", mphys_meta_path, "top-level metadata", "candidate_excluded_n",
            "Compound candidates lacking at least one physical coordinate; the retained/excluded audit is reported in the SI.",
        ),
        (
            "R9_MPHYS_EXCLUDED_MP_MATCHED_POOL_EVALUABLE_N", "MP_matched_pool_evaluable_n_in_excluded_candidates",
            int(mphys_audit[(mphys_audit.group.eq("candidate excluded")) & (mphys_audit.feature.eq("MP matched-pool stable fraction"))].iloc[0].n_evaluable),
            "31 compound candidates excluded from Mphys", mphys_audit_path,
            'group == "candidate excluded" and feature == "MP matched-pool stable fraction"', "n_evaluable",
            "The excluded candidates are non-random with respect to matched-pool coordinate coverage.",
        ),
    ):
        rows.append(row(claim_id, "supplementary", quantity, value, "rows", denominator, source_file, selector, source_column, interpretation))

    materials_path = OUT / "figure_sources" / "fig3_materials_chemistry_strata.csv"
    materials = pd.read_csv(materials_path)
    materials_claims = (
        ("B1_MATERIALS_BINARY_DISCORDANCE_RATE", "Binary"),
        ("B2_MATERIALS_TERNARY_DISCORDANCE_RATE", "Ternary"),
        ("B3_MATERIALS_QUATERNARY_PLUS_DISCORDANCE_RATE", "Quaternary+"),
        ("B4_MATERIALS_LANTHANIDE_DISCORDANCE_RATE", "Lanthanide"),
        ("B5_MATERIALS_HALOGEN_DISCORDANCE_RATE", "Halogen"),
        ("B6_MATERIALS_NO_OXYGEN_DISCORDANCE_RATE", "No oxygen"),
        ("B7_MATERIALS_OXYGEN_DISCORDANCE_RATE", "Oxygen"),
    )
    for claim_id, stratum in materials_claims:
        record = materials[materials.stratum.eq(stratum)].iloc[0]
        rows.append(
            row(
                claim_id, "results", "MP--Alexandria-PBE_zero_threshold_discordance_rate",
                float(record.discordance_rate), "fraction", f"D2 rows in {stratum} stratum",
                materials_path, f'stratum == "{stratum}"', "discordance_rate",
                "Descriptive chemistry stratum; overlapping descriptors do not identify a mechanism.",
            )
        )

    matching_path = OUT / "matching_sensitivity" / "matching_sensitivity_summary.csv"
    matching = pd.read_csv(matching_path)
    for record in matching.itertuples(index=False):
        for column in (
            "d1_retained_n", "d2_retained_n", "mphys_tolerance_specific_n",
            "equivalence_class_n", "non_singleton_equivalence_class_n",
            "largest_equivalence_class_n",
        ):
            rows.append(
                row(
                    f"S1_MATCH_{record.matching_tolerance.upper()}_{column.upper()}", "supplementary",
                    column, int(getattr(record, column)), "rows" if column.endswith("_n") else "count",
                    f"{record.matching_tolerance} matching sensitivity",
                    matching_path, f'matching_tolerance == "{record.matching_tolerance}"', column,
                    "Cross-source counts are frozen-mapping survival; equivalence counts rebuild the full D5 graph.",
                )
            )

    claim_map = pd.DataFrame(rows)
    if claim_map["claim_id"].duplicated().any():
        raise RuntimeError("Claim identifiers must be unique")
    claim_map.to_csv(OUT / "claim_to_output_map.csv", index=False)
    metadata = {
        "status": "figure_and_claim_lock_complete",
        "claim_n": int(len(claim_map)),
        "unique_source_file_n": int(claim_map.source_file.nunique()),
        "all_claim_ids_unique": True,
        "all_rows_locked": bool(
            claim_map.lock_status.eq("locked_to_unique_machine_readable_source").all()
        ),
    }
    (OUT / "claim_to_output_map.json").write_text(
        json.dumps({"metadata": metadata, "claims": claim_map.to_dict("records")}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
