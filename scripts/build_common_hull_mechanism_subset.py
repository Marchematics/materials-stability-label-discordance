from __future__ import annotations

import csv
import hashlib
import json
import os
import time
import zipfile
from pathlib import Path
from collections.abc import Iterable
from typing import Any

import pandas as pd
from pymatgen.analysis.phase_diagram import PDEntry, PhaseDiagram
from pymatgen.core import Composition


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "common_hull_mechanism_subset"
ALEX_ZIP = Path("/home/waas/paper_experiments/private/mattergen_repo/data-release/alex-mp/alex_mp_20.zip")
MP_CHEMSYS_CACHE = OUT / "mp_chemsys_summary_cache.jsonl"

SAMPLE_SEED = 20260523
N_DISCORDANT = 1000
N_CONCORDANT_CONTROL = 500


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


def reduced_formula(formula: str) -> str:
    try:
        return Composition(str(formula)).reduced_formula
    except Exception:
        return str(formula)


def load_target_sample() -> pd.DataFrame:
    df = pd.read_csv(FULL / "table_full_mp_alex_structure_matches.csv")
    df = df[df["match_status"].eq("strict_structure_match")].copy()
    df["mp_e_above_hull"] = pd.to_numeric(df["mp_e_above_hull"], errors="coerce")
    df["alex_e_above_hull"] = pd.to_numeric(df["alex_e_above_hull"], errors="coerce")
    df["mp_stable"] = df["mp_stable_exact"].astype(str).str.lower().eq("true")
    df["alex_stable"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["native_discordant"] = df["mp_stable"] != df["alex_stable"]
    df["abs_delta_ehull"] = (df["mp_e_above_hull"] - df["alex_e_above_hull"]).abs()
    discordant = df[df["native_discordant"]].sample(
        n=min(N_DISCORDANT, int(df["native_discordant"].sum())),
        random_state=SAMPLE_SEED,
    )
    controls = df[~df["native_discordant"]].sample(
        n=min(N_CONCORDANT_CONTROL, int((~df["native_discordant"]).sum())),
        random_state=SAMPLE_SEED,
    )
    sample = pd.concat(
        [
            discordant.assign(sample_role="discordant_mechanism_sample"),
            controls.assign(sample_role="concordant_control_sample"),
        ],
        ignore_index=True,
    ).sort_values(["sample_role", "chemical_system", "material_id"])
    sample["target_reduced_formula"] = sample["formula"].map(reduced_formula)
    OUT.mkdir(parents=True, exist_ok=True)
    sample[
        [
            "sample_role",
            "material_id",
            "formula",
            "target_reduced_formula",
            "chemical_system",
            "mp_e_above_hull",
            "alex_e_above_hull",
            "mp_stable",
            "alex_stable",
            "native_discordant",
            "abs_delta_ehull",
        ]
    ].to_csv(OUT / "table_common_hull_mechanism_sample.csv", index=False)
    return sample


def load_alex_ref() -> pd.DataFrame:
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        with zf.open("ref.csv") as f:
            ref = pd.read_csv(f, low_memory=False)
    ref = ref.dropna(subset=["structure_id", "reduced_formula", "energy", "num_sites"]).copy()
    ref["reduced_formula_norm"] = ref["reduced_formula"].map(reduced_formula)
    ref = ref[ref["reduced_formula_norm"].astype(str).ne("nan")].copy()
    ref["energy_per_atom"] = pd.to_numeric(ref["energy"], errors="coerce") / pd.to_numeric(
        ref["num_sites"], errors="coerce"
    )
    def is_element_formula(formula: str) -> bool:
        try:
            return len(Composition(str(formula)).elements) == 1
        except Exception:
            return False

    element_rows = ref[ref["reduced_formula_norm"].map(is_element_formula)].copy()
    element_ref = element_rows.groupby("reduced_formula_norm")["energy_per_atom"].min().to_dict()

    def formation_per_atom(row: pd.Series) -> float | None:
        try:
            comp = Composition(str(row["reduced_formula_norm"]))
            total = 0.0
            atoms = comp.num_atoms
            for el, amt in comp.items():
                val = element_ref.get(str(el))
                if val is None:
                    return None
                total += float(amt) / atoms * float(val)
            return float(row["energy_per_atom"]) - total
        except Exception:
            return None

    ref["formation_energy_per_atom_proxy"] = ref.apply(formation_per_atom, axis=1)
    ref = ref.dropna(subset=["formation_energy_per_atom_proxy"]).copy()

    def element_tuple(formula: str) -> tuple[str, ...] | None:
        try:
            return tuple(sorted(str(el) for el in Composition(str(formula)).elements))
        except Exception:
            return None

    ref["element_tuple"] = ref["reduced_formula_norm"].map(element_tuple)
    ref = ref[ref["element_tuple"].notna()].copy()
    return ref


def build_alex_formula_index(ref: pd.DataFrame, chemical_systems: Iterable[str]) -> dict[str, dict[str, float]]:
    """Precompute lowest Alexandria formation-energy proxy per formula for each target chemical system."""
    formula_groups = (
        ref.groupby(["element_tuple", "reduced_formula_norm"])["formation_energy_per_atom_proxy"]
        .min()
        .reset_index()
    )
    grouped: list[tuple[set[str], str, float]] = [
        (set(elements), str(row.reduced_formula_norm), float(row.formation_energy_per_atom_proxy))
        for row in formula_groups.itertuples(index=False)
        for elements in [tuple(row.element_tuple)]
    ]
    out: dict[str, dict[str, float]] = {}
    systems = list(chemical_systems)
    for i, cs in enumerate(systems, start=1):
        elements = set(str(cs).split("-"))
        best: dict[str, float] = {}
        for formula_elements, formula, energy in grouped:
            if formula_elements.issubset(elements):
                best[formula] = min(energy, best.get(formula, float("inf")))
        out[cs] = best
        if i % 250 == 0 or i == len(systems):
            print(f"Indexed Alexandria common-formula candidates {i}/{len(systems)}", flush=True)
    return out


def read_mp_cache() -> dict[str, list[dict[str, Any]]]:
    if not MP_CHEMSYS_CACHE.exists():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    with MP_CHEMSYS_CACHE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            out[str(row["chemical_system"])] = row["entries"]
    return out


def fetch_mp_chemsys(chemical_systems: list[str]) -> dict[str, list[dict[str, Any]]]:
    from mp_api.client import MPRester

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY is required; source /root/.mp_api_env before running.")
    OUT.mkdir(parents=True, exist_ok=True)
    cache = read_mp_cache()
    todo = [cs for cs in chemical_systems if cs not in cache]
    print(f"MP chemsys cache: done={len(cache)} todo={len(todo)} total={len(chemical_systems)}", flush=True)
    if not todo:
        return cache
    with MPRester(api_key) as mpr, MP_CHEMSYS_CACHE.open("a", encoding="utf-8") as out:
        for idx, cs in enumerate(todo, start=1):
            docs = mpr.materials.summary.search(
                chemsys=cs,
                fields=[
                    "material_id",
                    "formula_pretty",
                    "formation_energy_per_atom",
                    "energy_above_hull",
                    "nsites",
                ],
            )
            entries = []
            for doc in docs:
                fepa = getattr(doc, "formation_energy_per_atom", None)
                if fepa is None:
                    continue
                entries.append(
                    {
                        "material_id": str(doc.material_id),
                        "formula": str(doc.formula_pretty),
                        "reduced_formula": reduced_formula(str(doc.formula_pretty)),
                        "formation_energy_per_atom": float(fepa),
                        "energy_above_hull": float(doc.energy_above_hull)
                        if getattr(doc, "energy_above_hull", None) is not None
                        else None,
                    }
                )
            row = {"chemical_system": cs, "entries": entries}
            out.write(json.dumps(row) + "\n")
            out.flush()
            cache[cs] = entries
            if idx % 25 == 0 or idx == len(todo):
                print(f"Fetched MP chemsys {idx}/{len(todo)} latest={cs} entries={len(entries)}", flush=True)
            time.sleep(0.1)
    return cache


def min_entries_by_formula(rows: Iterable[dict[str, Any]], energy_key: str) -> dict[str, float]:
    best: dict[str, float] = {}
    for row in rows:
        formula = reduced_formula(str(row["reduced_formula"]))
        energy = row.get(energy_key)
        if energy is None or pd.isna(energy):
            continue
        best[formula] = min(float(energy), best.get(formula, float("inf")))
    return best


def e_above_common_hull(formula: str, target_fepa: float, competitor_fepa: dict[str, float]) -> float | None:
    formula = reduced_formula(formula)
    formulas = dict(competitor_fepa)
    formulas[formula] = min(float(target_fepa), formulas.get(formula, float("inf")))
    try:
        entries = []
        for f, fepa in formulas.items():
            comp = Composition(f)
            entries.append(PDEntry(comp, float(fepa) * comp.num_atoms))
        target = PDEntry(Composition(formula), float(target_fepa) * Composition(formula).num_atoms)
        pdia = PhaseDiagram(entries + [target])
        return float(pdia.get_e_above_hull(target))
    except Exception:
        return None


def build_results(
    sample: pd.DataFrame,
    alex_ref: pd.DataFrame,
    mp_cache: dict[str, list[dict[str, Any]]],
    alex_formula_index: dict[str, dict[str, float]],
) -> pd.DataFrame:
    alex_target = alex_ref.drop_duplicates("structure_id").set_index("structure_id")
    rows = []
    print(f"Building common-composition mechanism rows for n={len(sample)}", flush=True)
    for i, row in enumerate(sample.itertuples(index=False), start=1):
        cs = row.chemical_system
        formula = reduced_formula(row.formula)
        mp_entries = mp_cache.get(cs, [])
        mp_best = min_entries_by_formula(mp_entries, "formation_energy_per_atom")
        alex_best = alex_formula_index.get(cs, {})
        common_formulas = set(mp_best) & set(alex_best)
        target_alex = alex_target.loc[row.material_id] if row.material_id in alex_target.index else None
        target_alex_fepa = (
            float(target_alex["formation_energy_per_atom_proxy"])
            if target_alex is not None and pd.notna(target_alex["formation_energy_per_atom_proxy"])
            else None
        )
        target_mp_fepa = None
        for entry in mp_entries:
            if str(entry["material_id"]) == str(row.material_id):
                target_mp_fepa = float(entry["formation_energy_per_atom"])
                break
        common_mp_ehull = (
            e_above_common_hull(formula, target_mp_fepa, {k: mp_best[k] for k in common_formulas})
            if target_mp_fepa is not None and formula in common_formulas
            else None
        )
        common_alex_ehull = (
            e_above_common_hull(formula, target_alex_fepa, {k: alex_best[k] for k in common_formulas})
            if target_alex_fepa is not None and formula in common_formulas
            else None
        )
        common_mp_stable = common_mp_ehull is not None and common_mp_ehull <= 1e-8
        common_alex_stable = common_alex_ehull is not None and common_alex_ehull <= 1e-8
        common_available = common_mp_ehull is not None and common_alex_ehull is not None
        if not common_available:
            mechanism = "common_hull_unavailable"
        elif bool(row.native_discordant) and common_mp_stable != common_alex_stable:
            mechanism = "energy_or_correction_driven_common_composition"
        elif bool(row.native_discordant) and common_mp_stable == common_alex_stable:
            mechanism = "competitor_set_or_reporting_sensitive"
        elif (not bool(row.native_discordant)) and common_mp_stable != common_alex_stable:
            mechanism = "hidden_common_set_sensitivity"
        else:
            mechanism = "concordant_under_native_and_common_composition"
        rows.append(
            {
                "sample_role": row.sample_role,
                "material_id": row.material_id,
                "formula": row.formula,
                "chemical_system": cs,
                "native_mp_ehull": row.mp_e_above_hull,
                "native_alex_ehull": row.alex_e_above_hull,
                "native_mp_stable": row.mp_stable,
                "native_alex_stable": row.alex_stable,
                "native_discordant": row.native_discordant,
                "mp_common_composition_ehull": common_mp_ehull,
                "alex_common_composition_ehull": common_alex_ehull,
                "mp_common_composition_stable": common_mp_stable if common_available else "",
                "alex_common_composition_stable": common_alex_stable if common_available else "",
                "common_formula_count": len(common_formulas),
                "mp_competitor_formula_count": len(mp_best),
                "alex_competitor_formula_count": len(alex_best),
                "mechanism_class": mechanism,
                "claim_scope": "common_composition_hull_proxy_subset",
            }
        )
        if i % 250 == 0:
            print(f"Mechanism rows {i}/{len(sample)}", flush=True)
    return pd.DataFrame(rows)


def write_summaries(results: pd.DataFrame) -> None:
    results.to_csv(OUT / "table_common_hull_mechanism_results.csv", index=False)
    coverage = (
        results.assign(common_available=results["mp_common_composition_ehull"].notna() & results["alex_common_composition_ehull"].notna())
        .groupby("sample_role")
        .agg(
            n=("material_id", "count"),
            common_available_n=("common_available", "sum"),
            median_common_formula_count=("common_formula_count", "median"),
            native_discordant_n=("native_discordant", "sum"),
        )
        .reset_index()
    )
    coverage["common_available_fraction"] = coverage["common_available_n"] / coverage["n"]
    coverage.to_csv(OUT / "table_common_hull_coverage_audit.csv", index=False)
    mechanism = (
        results.groupby(["sample_role", "mechanism_class"])
        .size()
        .rename("n")
        .reset_index()
    )
    mechanism["fraction_within_sample_role"] = mechanism["n"] / mechanism.groupby("sample_role")["n"].transform("sum")
    mechanism.to_csv(OUT / "table_common_hull_mechanism_decomposition.csv", index=False)
    examples = (
        results[results["native_discordant"].astype(bool)]
        .sort_values(["mechanism_class", "common_formula_count"], ascending=[True, False])
        .groupby("mechanism_class")
        .head(5)
    )
    examples.to_csv(OUT / "table_common_hull_representative_cases.csv", index=False)
    (OUT / "COMMON_HULL_MECHANISM_SUBSET_CLOSEOUT.md").write_text(
        "# Common-Composition Hull Mechanism Subset\n\n"
        "This milestone converts the prior common-hull protocol into a completed, deterministic subset analysis. "
        "It is intentionally labelled as a common-composition competitor-hull proxy because third-source/exact competitor structure matching and unclipped source energies are not yet complete.\n\n"
        "The completed subset is a coverage-boundary result, not a positive mechanism-decomposition result. "
        "Under the public source-native tables available here, only a small fraction of sampled MP-Alex matched targets has a common-composition competitor set with both MP and Alexandria proxy formation energies. "
        "The result therefore supports the claim that full mechanism attribution requires a dedicated common-hull reconstruction or additional unclipped source-energy exports, rather than a lightweight table join.\n\n"
        f"{coverage.to_markdown(index=False)}\n\n"
        f"{mechanism.to_markdown(index=False)}\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sample = load_target_sample()
    alex_ref = load_alex_ref()
    chemsys = sorted(sample["chemical_system"].unique())
    mp_cache = fetch_mp_chemsys(chemsys)
    alex_formula_index = build_alex_formula_index(alex_ref, chemsys)
    results = build_results(sample, alex_ref, mp_cache, alex_formula_index)
    write_summaries(results)
    write_manifest()


if __name__ == "__main__":
    main()
