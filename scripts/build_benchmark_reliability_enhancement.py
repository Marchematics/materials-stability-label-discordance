from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import pandas as pd
from pymatgen.core import Composition


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "benchmark_reliability_enhancement"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> None:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "MANIFEST_SHA256.txt":
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_full_denominator() -> pd.DataFrame:
    df = pd.read_csv(FULL / "table_full_mp_alex_structure_matches.csv")
    df = df[df["match_status"].eq("strict_structure_match")].copy()
    df["mp_e_above_hull"] = pd.to_numeric(df["mp_e_above_hull"], errors="coerce")
    df["alex_e_above_hull"] = pd.to_numeric(df["alex_e_above_hull"], errors="coerce")
    df["mp_stable"] = df["mp_stable_exact"].astype(str).str.lower().eq("true")
    df["alex_stable"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["discordant"] = df["mp_stable"] != df["alex_stable"]
    df["direction"] = "concordant"
    df.loc[df["mp_stable"] & ~df["alex_stable"], "direction"] = "mp_stable_alex_unstable"
    df.loc[~df["mp_stable"] & df["alex_stable"], "direction"] = "mp_unstable_alex_stable"
    df["abs_delta_ehull"] = (df["mp_e_above_hull"] - df["alex_e_above_hull"]).abs()
    df["either_near_hull_25mev"] = (df["mp_e_above_hull"].abs() <= 0.025) | (
        df["alex_e_above_hull"].abs() <= 0.025
    )
    df["both_far_25mev"] = ~df["either_near_hull_25mev"]
    return df


def summarize_condition(df: pd.DataFrame, name: str, mask: pd.Series, role: str) -> dict[str, object]:
    sub = df[mask].copy()
    n = int(len(sub))
    discordant = int(sub["discordant"].sum()) if n else 0
    mp_only = int((sub["direction"].eq("mp_stable_alex_unstable")).sum()) if n else 0
    alex_only = int((sub["direction"].eq("mp_unstable_alex_stable")).sum()) if n else 0
    return {
        "selection_condition": name,
        "role": role,
        "n": n,
        "discordant_n": discordant,
        "discordance_rate": discordant / n if n else "",
        "mp_stable_alex_unstable_n": mp_only,
        "mp_unstable_alex_stable_n": alex_only,
        "directionality_balance_mp_minus_alex": mp_only - alex_only,
        "median_abs_delta_ehull": float(sub["abs_delta_ehull"].median()) if n else "",
        "claim_scope": "completed_full_denominator_selection_atlas",
    }


def element_tags(formula: str) -> set[str]:
    try:
        return {str(el) for el in Composition(formula).elements}
    except Exception:
        return set()


def build_selection_atlas(df: pd.DataFrame) -> None:
    rows: list[dict[str, object]] = []
    rows.append(summarize_condition(df, "full_denominator", pd.Series(True, index=df.index), "baseline"))
    rows.append(summarize_condition(df, "MP_exact_stable", df["mp_stable"], "source_native_selection"))
    rows.append(summarize_condition(df, "Alex_exact_stable", df["alex_stable"], "source_native_selection"))
    rows.append(
        summarize_condition(
            df,
            "MP_or_Alex_near_hull_25meV",
            df["either_near_hull_25mev"],
            "boundary_selection",
        )
    )
    rows.append(
        summarize_condition(
            df,
            "far_from_hull_concordant_stable_25meV",
            df["both_far_25mev"] & df["mp_stable"] & df["alex_stable"],
            "high_confidence_region",
        )
    )
    rows.append(
        summarize_condition(
            df,
            "far_from_hull_concordant_unstable_25meV",
            df["both_far_25mev"] & ~df["mp_stable"] & ~df["alex_stable"],
            "high_confidence_region",
        )
    )
    for label, elements in {
        "oxygen_containing": {"O"},
        "halogen_containing": {"F", "Cl", "Br", "I"},
        "lanthanide_containing": {
            "La",
            "Ce",
            "Pr",
            "Nd",
            "Pm",
            "Sm",
            "Eu",
            "Gd",
            "Tb",
            "Dy",
            "Ho",
            "Er",
            "Tm",
            "Yb",
            "Lu",
        },
        "transition_metal_containing": {
            "Sc",
            "Ti",
            "V",
            "Cr",
            "Mn",
            "Fe",
            "Co",
            "Ni",
            "Cu",
            "Zn",
            "Y",
            "Zr",
            "Nb",
            "Mo",
            "Tc",
            "Ru",
            "Rh",
            "Pd",
            "Ag",
            "Cd",
            "Hf",
            "Ta",
            "W",
            "Re",
            "Os",
            "Ir",
            "Pt",
            "Au",
            "Hg",
        },
    }.items():
        mask = df["formula"].map(lambda f, elems=elements: bool(element_tags(str(f)) & elems))
        rows.append(summarize_condition(df, label, mask, "chemistry_stratum"))
    pd.DataFrame(rows).to_csv(OUT / "table_selection_conditioned_discordance_atlas.csv", index=False)


def threshold_sweep(df: pd.DataFrame) -> None:
    rows = []
    total_discordant = int(df["discordant"].sum())
    for mev in [5, 10, 25, 50, 100]:
        threshold = mev / 1000.0
        flag = (df["mp_e_above_hull"].abs() <= threshold) | (df["alex_e_above_hull"].abs() <= threshold)
        flagged = df[flag]
        captured = int((flag & df["discordant"]).sum())
        rows.append(
            {
                "threshold_meV_atom": mev,
                "flagged_n": int(flag.sum()),
                "flagged_fraction": float(flag.mean()),
                "discordant_captured_n": captured,
                "discordant_total_n": total_discordant,
                "discordant_recall": captured / total_discordant if total_discordant else "",
                "outside_discordant_n": int((~flag & df["discordant"]).sum()),
                "concordant_flagged_n": int((flag & ~df["discordant"]).sum()),
                "flag_precision_for_discordance": captured / len(flagged) if len(flagged) else "",
                "claim_scope": "full_denominator_reporting_burden_curve",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "table_full_denominator_uncertainty_threshold_sweep.csv", index=False)


def choose_cases(df: pd.DataFrame) -> pd.DataFrame:
    discordant = df[df["discordant"]].copy()
    pools: list[pd.DataFrame] = []
    pools.append(discordant.sort_values("abs_delta_ehull", ascending=False).head(8).assign(case_reason="largest_delta_ehull"))
    pools.append(discordant.sort_values("abs_delta_ehull", ascending=True).head(8).assign(case_reason="smallest_delta_ehull_flip"))
    for direction in ["mp_stable_alex_unstable", "mp_unstable_alex_stable"]:
        pools.append(
            discordant[discordant["direction"].eq(direction)]
            .sort_values("abs_delta_ehull", ascending=False)
            .head(6)
            .assign(case_reason=f"largest_delta_{direction}")
        )
    oxygen = discordant[discordant["formula"].map(lambda f: "O" in element_tags(str(f)))]
    pools.append(oxygen.sort_values("abs_delta_ehull", ascending=False).head(6).assign(case_reason="oxygen_discordant"))
    cases = pd.concat(pools, ignore_index=True)
    cases = cases.drop_duplicates("material_id").head(24)
    cols = [
        "case_reason",
        "material_id",
        "formula",
        "chemical_system",
        "num_sites",
        "mp_e_above_hull",
        "alex_e_above_hull",
        "abs_delta_ehull",
        "direction",
        "mp_stable",
        "alex_stable",
        "alex_source_file",
    ]
    return cases[cols]


def write_case_atlas(df: pd.DataFrame) -> None:
    choose_cases(df).to_csv(OUT / "table_materials_case_atlas.csv", index=False)


def write_benchmark_card() -> None:
    rows = [
        ("label_source", "Materials Project and Alexandria source-native labels", "completed"),
        ("database_version", "Alexandria alex-mp v20 plus MP API-derived records queried during the full run", "completed"),
        ("query_date", "Recorded in full_run_tmux.log and artifact manifest", "completed"),
        ("api_endpoint", "MP materials summary search by MP material_id", "completed"),
        ("structure_matching_protocol", "pymatgen StructureMatcher ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=True", "completed"),
        ("hull_reference", "source-native public e_above_hull values", "completed"),
        ("stability_threshold", "exact stable if e_above_hull <= 0 eV/atom", "completed"),
        ("source_discordance_burden", "5,060 / 43,139 = 0.1173 on strict MP-Alex matches", "completed"),
        ("near_threshold_burden", "reported by full-denominator threshold sweep", "completed"),
        ("conflict_excluded_metric", "protocol item for model benchmarks; not a completed full-denominator model-ranking result", "protocol_only"),
        ("conflict_included_metric", "protocol item for model benchmarks; not a completed full-denominator model-ranking result", "protocol_only"),
        ("exact_denominator_definition", "43,139 strict MP-Alex structure matches from 43,984 Alexandria rows with MP identifiers", "completed"),
        ("missing_id_audit", "815 missing MP records and 30 structure mismatches", "completed"),
    ]
    pd.DataFrame(rows, columns=["card_field", "paper_value", "status"]).to_csv(
        OUT / "table_source_aware_benchmark_card.csv", index=False
    )


def write_gated_protocols() -> None:
    pd.DataFrame(
        [
            {
                "protocol_component": "common_hull_reconstruction",
                "status": "gated_protocol_not_completed",
                "required_inputs": "unclipped formation energies and sufficient competing entries for MP and Alexandria chemical systems",
                "completed_claim_allowed": False,
                "intended_output": "waterfall separating energy/correction flips from competitor-set flips",
            },
            {
                "protocol_component": "source_energy_on_common_competitor_set",
                "status": "gated_protocol_not_completed",
                "required_inputs": "source-specific formation energies mapped onto a shared competitor set",
                "completed_claim_allowed": False,
                "intended_output": "mechanistic decomposition of native discordance",
            },
            {
                "protocol_component": "public_table_clipping_assessment",
                "status": "partial_reporting_burden_only",
                "required_inputs": "unclipped source energies to go beyond near-hull flag burden",
                "completed_claim_allowed": False,
                "intended_output": "separate reporting artifacts from physical hull shifts",
            },
        ]
    ).to_csv(OUT / "table_common_hull_mechanism_protocol.csv", index=False)
    pd.DataFrame(
        [
            {
                "source": "JARVIS",
                "status": "protocol_candidate",
                "matching_route": "formula query followed by the same strict StructureMatcher",
                "main_text_gate": "n_strict_matches >= 1000",
                "supplement_gate": "200 <= n_strict_matches < 1000",
                "coverage_boundary_gate": "n_strict_matches < 200",
            },
            {
                "source": "OQMD",
                "status": "protocol_candidate_after_prior_ID_route_undercovered",
                "matching_route": "formula query followed by the same strict StructureMatcher",
                "main_text_gate": "n_strict_matches >= 1000",
                "supplement_gate": "200 <= n_strict_matches < 1000",
                "coverage_boundary_gate": "n_strict_matches < 200",
            },
            {
                "source": "AFLOW_or_OPTIMADE_source",
                "status": "protocol_candidate_if_comparable_ehull_available",
                "matching_route": "formula query followed by the same strict StructureMatcher",
                "main_text_gate": "n_strict_matches >= 1000",
                "supplement_gate": "200 <= n_strict_matches < 1000",
                "coverage_boundary_gate": "n_strict_matches < 200",
            },
        ]
    ).to_csv(OUT / "table_third_source_expansion_protocol.csv", index=False)
    pd.DataFrame(
        [
            {
                "benchmark_impact_component": "full_denominator_model_predictions",
                "status": "gated_protocol_not_completed",
                "required_condition": "frozen public or reproducibly generated predictions on the same 43,139 strict-match denominator",
                "allowed_metrics": "precision@K; stable_rate@K; recall; F1; AUROC; AUPRC; Kendall/Spearman ranking stability",
                "claim_boundary": "no full-denominator model leaderboard claim until this gate is met",
            },
            {
                "benchmark_impact_component": "source_conflict_excluded_metrics",
                "status": "protocol_defined_not_completed",
                "required_condition": "eligible model predictions on full denominator",
                "allowed_metrics": "metric uncertainty band under MP labels, Alexandria labels and conflict-excluded labels",
                "claim_boundary": "may support benchmark-impact claim only after model-prediction gate",
            },
        ]
    ).to_csv(OUT / "table_benchmark_impact_protocol.csv", index=False)


def write_closeout() -> None:
    summary = pd.read_csv(FULL / "table_full_mp_alex_denominator_summary.csv").iloc[0]
    atlas = pd.read_csv(OUT / "table_selection_conditioned_discordance_atlas.csv")
    full_row = atlas[atlas["selection_condition"].eq("full_denominator")].iloc[0]
    mp_stable = atlas[atlas["selection_condition"].eq("MP_exact_stable")].iloc[0]
    alex_stable = atlas[atlas["selection_condition"].eq("Alex_exact_stable")].iloc[0]
    text = f"""# Benchmark Reliability Enhancement

This milestone adds completed full-denominator reporting enhancements and freezes gated protocols for mechanism, third-source and benchmark-impact extensions. It does not downgrade the 43,139 strict-match result and does not add a new model benchmark.

## Completed from existing full denominator

- Strict MP-Alex matches: {int(summary['strict_structure_matches']):,}
- Discordant exact-stability labels: {int(summary['discordant_n']):,}
- Full-denominator discordance: {float(summary['discordance_rate']):.4f}
- MP-exact-stable selected subset discordance: {float(mp_stable['discordance_rate']):.4f} (n={int(mp_stable['n']):,})
- Alex-exact-stable selected subset discordance: {float(alex_stable['discordance_rate']):.4f} (n={int(alex_stable['n']):,})

Completed tables:

- `table_selection_conditioned_discordance_atlas.csv`
- `table_full_denominator_uncertainty_threshold_sweep.csv`
- `table_materials_case_atlas.csv`
- `table_source_aware_benchmark_card.csv`

## Frozen but not completed

- `table_common_hull_mechanism_protocol.csv` defines the common-hull/common-competitor mechanism decomposition gate.
- `table_third_source_expansion_protocol.csv` defines formula-query plus strict StructureMatcher third-source expansion gates.
- `table_benchmark_impact_protocol.csv` defines the full-denominator model-prediction gate for benchmark-impact claims.

Claim boundary: these gated protocols cannot be cited as completed mechanism, triangulation or full-denominator model-ranking evidence until their required inputs and outputs exist.
"""
    (OUT / "BENCHMARK_RELIABILITY_ENHANCEMENT_CLOSEOUT.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_full_denominator()
    build_selection_atlas(df)
    threshold_sweep(df)
    write_case_atlas(df)
    write_benchmark_card()
    write_gated_protocols()
    write_closeout()
    write_manifest()


if __name__ == "__main__":
    main()
