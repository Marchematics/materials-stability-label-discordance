#!/usr/bin/env python3
"""Build an integrity manifest and provisional claim ledger for revision v3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    summary = json.loads((OUT / "evaluation" / "evaluation_summary.json").read_text())
    equivalence = json.loads((OUT / "structural_equivalence_metadata.json").read_text())
    tie = pd.read_csv(OUT / "evaluation" / "ranking_tie_audit_all_models.csv")
    old_tie = pd.read_csv(
        OUT / "superseded_ranking_audit" / "previous_self_included_hull_tie_audit.csv"
    )
    threshold = pd.read_csv(OUT / "evaluation" / "endpoint_threshold_scan.csv")
    indeterminate = pd.read_csv(OUT / "evaluation" / "indeterminate_zone_conflicts.csv")
    topk = pd.read_csv(OUT / "evaluation" / "tie_aware_topk_physical_endpoints.csv")
    winner = pd.read_csv(OUT / "bootstrap" / "model_winner_frequencies_cluster_bootstrap.csv")
    regret = pd.read_csv(OUT / "bootstrap" / "endpoint_selection_regret_cluster_bootstrap.csv")
    budget = pd.read_csv(OUT / "evaluation" / "budget_sensitivity_audit.csv")
    matching = pd.read_csv(OUT / "matching_sensitivity" / "matching_sensitivity_summary.csv")
    materials = pd.read_csv(OUT / "figure_sources" / "fig3_materials_chemistry_strata.csv")
    source_card = pd.read_csv(OUT / "source_input_card" / "source_input_card.csv")
    mphys_exclusion = pd.read_csv(
        OUT / "mphys_support_exclusion_audit" / "mphys_retained_excluded_summary.csv"
    )

    native = threshold[
        threshold.support.eq("D2_native_full")
        & threshold.threshold_meV_per_atom.isin([0, 25, 50])
    ]
    claims = {
        "status": "core_analysis_complete_figure_and_claim_lock_complete_manuscript_revision_in_progress",
        "claims": [
            {
                "id": "C1_previous_topk_withdrawn",
                "claim": "The previous self-included predicted-hull top-1000 results are withdrawn because every model's K=1000 boundary lay inside a large zero-score tie.",
                "evidence": {
                    row.model_name: int(row.boundary_tie_n)
                    for row in old_tie[old_tie.K.eq(1000)].itertuples()
                },
            },
            {
                "id": "C2_repaired_ranking_ties",
                "claim": "The batch-relative equivalence-class-excluded signed reference-hull rankings have no tied K=1000 boundary on Mphys at 12-decimal score precision.",
                "evidence": {
                    "mphys_n": summary["mphys_n"],
                    "largest_tie_block_across_models": int(tie.largest_tie_block_n.max()),
                    "k1000_boundary_tie_sizes": {
                        row.model_name: int(row.boundary_tie_n)
                        for row in tie[tie.K.eq(1000)].itertuples()
                    },
                },
            },
            {
                "id": "C3_threshold_attenuation",
                "claim": "Native-coordinate disagreement decreases as a common stability tolerance is widened, but remains measurable at 25 and 50 meV per atom.",
                "evidence": {
                    str(int(threshold_mev)): {
                        "minimum_pair_rate": float(group.switch_rate.min()),
                        "maximum_pair_rate": float(group.switch_rate.max()),
                    }
                    for threshold_mev, group in native.groupby("threshold_meV_per_atom")
                },
            },
            {
                "id": "C4_indeterminate_robust_conflict",
                "claim": "Definite stable-versus-definite unstable MP/Alexandria-PBE conflicts remain after introducing an indeterminate near-hull zone, with the retained count and coverage reported jointly.",
                "evidence": indeterminate[
                    indeterminate.support.eq("D2_reconstructable")
                    & indeterminate.endpoint_a.eq("mp_source_coordinate")
                    & indeterminate.endpoint_b.eq("alex_pbe_source_coordinate")
                ][
                    [
                        "indeterminate_width_meV_per_atom", "decisive_n", "robust_conflict_n",
                        "robust_conflict_rate_full_support", "robust_conflict_rate_decisive_support",
                    ]
                ].to_dict("records"),
            },
            {
                "id": "C5_global_ranking_winner",
                "claim": "At the official zero-threshold endpoints, MACE-MP remains the point and bootstrap winner for AUROC, AP, and normalized AP across all five physical coordinates.",
                "evidence": winner[
                    winner.threshold_meV_per_atom.eq(0)
                    & winner.metric.isin(["auroc", "ap", "normalized_ap"])
                    & winner.model_name.eq("MACE-MP")
                ][["coordinate_endpoint", "metric", "winner_frequency"]].to_dict("records"),
            },
            {
                "id": "C6_topk_selection_is_endpoint_dependent_but_regret_small",
                "claim": "At K=1000, point winners change across physical endpoints, while MP-selected-model bootstrap regret is generally small and must be reported with its cohort interval.",
                "evidence": {
                    "point_hits_t0": topk[
                        topk.threshold_meV_per_atom.eq(0) & topk.K.eq(1000)
                    ][["model_name", "coordinate_endpoint", "expected_stable_hits"]].to_dict("records"),
                    "bootstrap_regret_t0": regret[
                        regret.threshold_meV_per_atom.eq(0)
                        & regret.metric.eq("expected_stable_hits_at_1000")
                    ].to_dict("records"),
                },
            },
            {
                "id": "C7_budget_specific_ordering",
                "claim": "Fine-grained top-K ordering changes with the validation budget, while MP-selection regret remains reported in absolute stable hits at every predeclared K.",
                "evidence": budget[
                    budget.threshold_meV_per_atom.eq(0) & budget.point_winner.astype(bool)
                ][
                    [
                        "K", "coordinate_endpoint", "model_name",
                        "point_first_second_margin_hits", "bootstrap_winner_frequency",
                        "bootstrap_regret_max_median_hits", "bootstrap_regret_max_ci_high_95_hits",
                    ]
                ].to_dict("records"),
            },
            {
                "id": "C8_matching_sensitivity",
                "claim": "The default matching setting reproduces the frozen D1 and D2 cohorts; tight/default/loose sensitivity reports denominator survival, equivalence-class size, and independently recomputed top-1000 rankings.",
                "evidence": matching.to_dict("records"),
            },
            {
                "id": "C9_materials_chemistry_strata",
                "claim": "Zero-threshold MP--Alexandria-PBE disagreement varies across broad, overlapping materials-chemistry descriptors; these descriptive strata do not identify a unique conflict mechanism.",
                "evidence": materials.to_dict("records"),
            },
            {
                "id": "C10_source_input_card",
                "claim": "The manuscript-visible source card identifies the continuous native hull field, formation-energy availability, unit and declared threshold for MP, MatterGen alex-mp-20 and official Alexandria-PBE.",
                "evidence": source_card.to_dict("records"),
            },
            {
                "id": "C11_mphys_retained_excluded_audit",
                "claim": "All model conclusions are conditional on the fixed Mphys support, with labels, size, reference-hull phase count, chemical-system coverage and element-family composition compared against excluded compound candidates.",
                "evidence": mphys_exclusion.to_dict("records"),
            },
        ],
    }
    (OUT / "provisional_claim_ledger.json").write_text(
        json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    files = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or "logs" in path.parts:
            continue
        if path.name == "manifest_referee_revision_v3.json":
            continue
        files.append(
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "name": "SourceAware-Stability referee revision v3 scientific analysis",
        "status": "manuscript_revision_in_progress",
        "estimand": "leave-one-tolerance-equivalence-class-out batch-relative transductive signed reference-hull margin",
        "candidate_pool": "frozen D5 four-score intersection; compound targets only",
        "reference_pool": "frozen D5 batch phases plus zero-formation elemental anchors",
        "evaluation_support": "Mphys formed only after all four rankings and five physical coordinates were generated",
        "endpoint_policy": "five row-defined physical coordinates; agreement, consensus, and audit policies excluded",
        "tie_policy": "analytic hypergeometric expectation and interval at rounded-12-decimal score ties",
        "equivalence": equivalence,
        "evaluation_summary": summary,
        "files": files,
    }
    (OUT / "manifest_referee_revision_v3.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"manifest_files": len(files), "claims": len(claims["claims"])}, indent=2))


if __name__ == "__main__":
    main()
