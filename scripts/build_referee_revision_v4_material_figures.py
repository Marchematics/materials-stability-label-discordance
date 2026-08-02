#!/usr/bin/env python3
"""Build compact material-discovery figures for the SourceAware revision.

This visual-only revision replaces generic grouped-bar layouts with source-hull
maps, chemistry-stratified forest plots, and compact point-interval summaries.
All numerical inputs are locked v3 tables; no scientific estimand is changed.
"""
from __future__ import annotations

from pathlib import Path
from math import sqrt
import json

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"
PHASE1 = ROOT / "outputs" / "phase1_v2"
FIG = OUT / "figures"
SRC = OUT / "figure_sources"

MODEL_ORDER = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
MODEL_COLORS = {
    "ALIGNN-FF": "#0072B2",
    "CHGNet": "#E69F00",
    "M3GNet": "#009E73",
    "MACE-MP": "#CC79A7",
}
ENDPOINT_LABELS = {
    "mp_source_coordinate": "MP native",
    "alexmp20_source_coordinate": "alex-mp-20 native",
    "alex_pbe_source_coordinate": "Alexandria-PBE native",
    "mp_matched_pool_coordinate": "MP matched pool",
    "alex_pbe_matched_pool_coordinate": "Alexandria-PBE matched pool",
}
PAIR_LABELS = {
    ("mp_source_coordinate", "alexmp20_source_coordinate"): "MP–alex-mp-20",
    ("mp_source_coordinate", "alex_pbe_source_coordinate"): "MP–Alexandria-PBE",
    ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"): "alex-mp-20–Alexandria-PBE",
}
PAIR_COLORS = {
    "MP–alex-mp-20": "#0072B2",
    "MP–Alexandria-PBE": "#D55E00",
    "alex-mp-20–Alexandria-PBE": "#009E73",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7.2,
    "axes.titlesize": 8.4,
    "axes.labelsize": 7.6,
    "xtick.labelsize": 6.6,
    "ytick.labelsize": 6.6,
    "axes.linewidth": 0.7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
})


def save(fig: plt.Figure, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext, kwargs in (
        ("pdf", {}),
        ("svg", {}),
        ("png", {"dpi": 450}),
        ("tiff", {"dpi": 600}),
    ):
        fig.savefig(FIG / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.025, **kwargs)
    plt.close(fig)


def source_hull_rows() -> pd.DataFrame:
    d = pd.read_parquet(PHASE1 / "source_union_hull_labels.parquet")
    cols = [
        "row_id", "formula", "chemical_system", "source_native_mp_ehull",
        "source_native_alex_pbe_ehull", "source_native_mp_label",
        "source_native_alex_pbe_label",
    ]
    d = d[cols].dropna().copy()
    d["discordant_zero_mev"] = d.source_native_mp_label.ne(d.source_native_alex_pbe_label)
    d["mp_ehull_mev"] = 1000 * d.source_native_mp_ehull.astype(float)
    d["alexandria_ehull_mev"] = 1000 * d.source_native_alex_pbe_ehull.astype(float)
    return d


def threshold_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    point = pd.read_csv(OUT / "evaluation" / "endpoint_threshold_scan.csv")
    point = point[
        point.support.eq("D2_native_full")
        & point.threshold_meV_per_atom.isin([0, 10, 25, 50])
    ].copy()
    boot = pd.read_csv(OUT / "bootstrap_conflicts" / "endpoint_threshold_cluster_bootstrap.csv")
    boot = boot[
        boot.support.eq("D2_native_full")
        & boot.threshold_meV_per_atom.isin([0, 10, 25, 50])
    ]
    scan = point.merge(
        boot,
        on=["support", "threshold_meV_per_atom", "endpoint_a", "endpoint_b"],
        validate="one_to_one",
    )
    scan["pair"] = [PAIR_LABELS[(a, b)] for a, b in zip(scan.endpoint_a, scan.endpoint_b)]

    ind = pd.read_csv(OUT / "evaluation" / "indeterminate_zone_conflicts.csv")
    ind = ind[
        ind.support.eq("D2_reconstructable")
        & ind.endpoint_a.eq("mp_source_coordinate")
        & ind.endpoint_b.eq("alex_pbe_source_coordinate")
    ].copy()
    ind_boot = pd.read_csv(OUT / "bootstrap_conflicts" / "indeterminate_cluster_bootstrap.csv")
    ind_boot = ind_boot[
        ind_boot.support.eq("D2_reconstructable")
        & ind_boot.endpoint_a.eq("mp_source_coordinate")
        & ind_boot.endpoint_b.eq("alex_pbe_source_coordinate")
    ]
    ind = ind.merge(
        ind_boot,
        on=["support", "indeterminate_width_meV_per_atom", "endpoint_a", "endpoint_b"],
        validate="one_to_one",
    )
    return scan, ind


def figure2() -> None:
    """Hull-coordinate map plus threshold and indeterminate sensitivity."""
    hull = source_hull_rows()
    scan, ind = threshold_tables()
    SRC.mkdir(parents=True, exist_ok=True)
    hull.to_csv(SRC / "fig2_mp_alexandria_hull_coordinate_map.csv", index=False)
    scan.to_csv(SRC / "fig2_threshold_scan.csv", index=False)
    ind.to_csv(SRC / "fig2_indeterminate_scan.csv", index=False)

    fig = plt.figure(figsize=(7.05, 2.55))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.35, 0.88, 0.88], wspace=0.52)
    a, b, c = [fig.add_subplot(grid[0, j]) for j in range(3)]

    lim = 120.0
    x = hull.mp_ehull_mev.clip(upper=lim).to_numpy()
    y = hull.alexandria_ehull_mev.clip(upper=lim).to_numpy()
    hb = a.hexbin(x, y, gridsize=38, bins="log", mincnt=1, cmap="Blues", linewidths=0, rasterized=True)
    q = hull.discordant_zero_mev.to_numpy()
    a.scatter(x[q], y[q], s=1.1, color="#D55E00", alpha=0.30, linewidths=0, rasterized=True, zorder=3)
    a.plot([0, lim], [0, lim], color="#5E6B7A", linewidth=0.75, linestyle=(0, (2, 2)))
    a.axvline(0, color="#F0B35A", linewidth=0.65, zorder=2)
    a.axhline(0, color="#F0B35A", linewidth=0.65, zorder=2)
    a.set(xlim=(-1, lim), ylim=(-1, lim), xlabel=r"MP $E_{\mathrm{hull}}$ (meV atom$^{-1}$)", ylabel=r"Alexandria-PBE $E_{\mathrm{hull}}$ (meV atom$^{-1}$)")
    a.set_title("a  Source-hull coordinates", loc="left", fontweight="bold", pad=3)
    a.spines[["top", "right"]].set_visible(False)
    cbar = fig.colorbar(hb, ax=a, fraction=0.045, pad=0.028)
    cbar.ax.tick_params(labelsize=5.8, length=2)
    cbar.set_label("row density", fontsize=6.2)

    for pair, group in scan.groupby("pair"):
        group = group.sort_values("threshold_meV_per_atom")
        xx = group.threshold_meV_per_atom.to_numpy()
        b.plot(xx, 100 * group.switch_rate, marker="o", markersize=2.8, linewidth=1.25, color=PAIR_COLORS[pair])
        b.fill_between(xx, 100 * group.switch_rate_ci_low_95, 100 * group.switch_rate_ci_high_95, color=PAIR_COLORS[pair], alpha=0.13, linewidth=0)
    b.set(xticks=[0, 10, 25, 50], xlabel="Threshold (meV atom$^{-1}$)", ylabel="Switch rate (%)", ylim=(5, 17))
    b.set_title("b  Threshold scan", loc="left", fontweight="bold", pad=3)
    b.spines[["top", "right"]].set_visible(False)
    b.grid(axis="y", color="#D9DDE3", linewidth=0.45)

    xx = ind.indeterminate_width_meV_per_atom.to_numpy()
    for col, color in (("robust_conflict_rate_full_support", "#D55E00"), ("robust_conflict_rate_decisive_support", "#0072B2")):
        c.plot(xx, 100 * ind[col], marker="o", markersize=2.8, linewidth=1.25, color=color)
        c.fill_between(xx, 100 * ind[f"{col}_ci_low_95"], 100 * ind[f"{col}_ci_high_95"], color=color, alpha=0.13, linewidth=0)
    c.set(xticks=[10, 30, 50], xlabel="Width (meV atom$^{-1}$)", ylabel="Robust conflict (%)")
    c.set_title("c  Decisive conflicts", loc="left", fontweight="bold", pad=3)
    c.spines[["top", "right"]].set_visible(False)
    c.grid(axis="y", color="#D9DDE3", linewidth=0.45)

    handles = [
        Line2D([0], [0], marker="o", color="#D55E00", linewidth=0, markersize=4, label="zero-threshold discordant row"),
        Line2D([0], [0], color="#5E6B7A", linestyle=(0, (2, 2)), linewidth=1, label="equal hull coordinate"),
    ]
    handles += [Line2D([0], [0], color=PAIR_COLORS[k], linewidth=1.3, label=k) for k in PAIR_COLORS]
    handles += [
        Line2D([0], [0], color="#D55E00", linewidth=1.3, label="all reconstructable rows"),
        Line2D([0], [0], color="#0072B2", linewidth=1.3, label="decisive rows"),
    ]
    fig.legend(handles=handles, ncol=4, loc="lower center", bbox_to_anchor=(0.51, -0.13), frameon=False, fontsize=5.65, columnspacing=0.95, handlelength=1.8)
    fig.subplots_adjust(left=0.074, right=0.99, bottom=0.26, top=0.93)
    save(fig, "fig2_revision_threshold_robustness")


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def chemistry_strata(hull: pd.DataFrame) -> pd.DataFrame:
    transition = {
        "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
        "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
        "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    }
    lanthanide = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
    halogen = {"F", "Cl", "Br", "I"}
    elems = hull.chemical_system.str.split("-")
    definitions = [
        ("Unary", lambda e: len(e) == 1),
        ("Binary", lambda e: len(e) == 2),
        ("Ternary", lambda e: len(e) == 3),
        ("Quaternary+", lambda e: len(e) >= 4),
        ("Transition metal", lambda e: bool(set(e) & transition)),
        ("No transition metal", lambda e: not bool(set(e) & transition)),
        ("Lanthanide", lambda e: bool(set(e) & lanthanide)),
        ("No lanthanide", lambda e: not bool(set(e) & lanthanide)),
        ("Oxygen", lambda e: "O" in e),
        ("No oxygen", lambda e: "O" not in e),
        ("Halogen", lambda e: bool(set(e) & halogen)),
        ("No halogen", lambda e: not bool(set(e) & halogen)),
    ]
    rows = []
    delta = (hull.mp_ehull_mev - hull.alexandria_ehull_mev).abs()
    for label, predicate in definitions:
        mask = np.array([predicate(e) for e in elems])
        n = int(mask.sum())
        k = int(hull.loc[mask, "discordant_zero_mev"].sum())
        low, high = wilson(k, n)
        rows.append({
            "stratum": label,
            "row_n": n,
            "discordant_n": k,
            "discordance_rate": k / n,
            "ci_low_95": low,
            "ci_high_95": high,
            "median_abs_hull_delta_mev": float(delta[mask].median()),
        })
    return pd.DataFrame(rows)


def figure3() -> None:
    """One-column chemistry forest plot; descriptive, not mechanistic."""
    hull = source_hull_rows()
    strata = chemistry_strata(hull)
    strata.to_csv(SRC / "fig3_materials_chemistry_strata.csv", index=False)
    baseline = hull.discordant_zero_mev.mean()

    fig, ax = plt.subplots(figsize=(3.18, 3.62))
    d = strata.iloc[::-1].reset_index(drop=True)
    yy = np.arange(len(d))
    colors = np.where(d.discordance_rate.to_numpy() >= baseline, "#D55E00", "#4C78A8")
    ax.errorbar(
        100 * d.discordance_rate,
        yy,
        xerr=np.vstack([100 * (d.discordance_rate - d.ci_low_95), 100 * (d.ci_high_95 - d.discordance_rate)]),
        fmt="none", ecolor="#AAB4C1", elinewidth=1.1, capsize=2, zorder=1,
    )
    ax.scatter(100 * d.discordance_rate, yy, s=30, c=colors, edgecolor="white", linewidth=0.45, zorder=2)
    ax.axvline(100 * baseline, color="#5E6B7A", linewidth=0.9, linestyle=(0, (4, 2)))
    ax.set_yticks(yy, d.stratum)
    ax.set_xlabel("MP–Alexandria-PBE discordance (%)")
    ax.set_xlim(0, max(18.5, 100 * d.ci_high_95.max() + 1.2))
    ax.set_title("Materials chemistry stratifies disagreement", loc="left", fontsize=8.2, fontweight="bold", pad=4)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#D9DDE3", linewidth=0.5)
    for y, n in zip(yy, d.row_n):
        ax.text(ax.get_xlim()[1] - 0.1, y, f"n={n:,}", ha="right", va="center", fontsize=5.4, color="#697586")
    fig.subplots_adjust(left=0.37, right=0.98, top=0.92, bottom=0.11)
    save(fig, "fig3_revision_materials_chemistry")


def figure4() -> None:
    """Compact point-interval model consequences; no grouped-bar panel."""
    topk = pd.read_csv(OUT / "evaluation" / "tie_aware_topk_physical_endpoints.csv")
    topk = topk[topk.threshold_meV_per_atom.eq(0) & topk.K.eq(1000)].copy()
    boot = pd.read_csv(OUT / "bootstrap" / "paired_metric_values_cluster_bootstrap.csv")
    boot = boot[
        boot.threshold_meV_per_atom.eq(0) & boot.metric.eq("expected_stable_hits_at_1000")
    ][["coordinate_endpoint", "model_name", "bootstrap_ci_low_95", "bootstrap_median", "bootstrap_ci_high_95"]]
    topk = topk.merge(boot, on=["coordinate_endpoint", "model_name"], validate="one_to_one")
    order = list(ENDPOINT_LABELS)
    topk["endpoint_order"] = topk.coordinate_endpoint.map({value: i for i, value in enumerate(order)})
    topk = topk.sort_values(["endpoint_order", "model_name"])
    topk.to_csv(SRC / "fig4_hits_at_1000.csv", index=False)

    budget = pd.read_csv(OUT / "evaluation" / "budget_sensitivity_audit.csv")
    decision = budget[budget.threshold_meV_per_atom.eq(0) & budget.K.eq(1000)].drop_duplicates("coordinate_endpoint").copy()
    decision["endpoint_order"] = decision.coordinate_endpoint.map({value: i for i, value in enumerate(order)})
    decision = decision.sort_values("endpoint_order")
    decision.to_csv(SRC / "fig4_margin_regret.csv", index=False)

    fig = plt.figure(figsize=(7.05, 2.38))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.0], wspace=0.55)
    a, b, c = [fig.add_subplot(grid[0, j]) for j in range(3)]
    yy = np.arange(len(order))
    for i, model in enumerate(MODEL_ORDER):
        q = topk[topk.model_name.eq(model)].set_index("coordinate_endpoint").loc[order]
        y = yy + (i - 1.5) * 0.12
        point = q.expected_stable_hits.to_numpy()
        a.errorbar(point, y, xerr=np.vstack([point - q.bootstrap_ci_low_95.to_numpy(), q.bootstrap_ci_high_95.to_numpy() - point]), fmt="o", color=MODEL_COLORS[model], markersize=3.1, capsize=1.4, linewidth=0.9, label=model)
    baseline = topk.drop_duplicates("coordinate_endpoint").set_index("coordinate_endpoint").loc[order]
    for y, value in zip(yy, baseline.random_expected_hits):
        a.vlines(value, y - 0.28, y + 0.28, color="#555555", linestyle=(0, (2, 2)), linewidth=1.0, zorder=0)
    a.set(yticks=yy, yticklabels=[ENDPOINT_LABELS[x] for x in order], xlabel="Stable hits at $K=1000$")
    a.invert_yaxis()
    a.set_title("a  Validation yield", loc="left", fontweight="bold", pad=3)
    a.spines[["top", "right"]].set_visible(False)
    a.grid(axis="x", color="#D9DDE3", linewidth=0.45)

    med = decision.first_second_margin_median_hits.to_numpy()
    low = decision.first_second_margin_ci_low_95_hits.to_numpy()
    high = decision.first_second_margin_ci_high_95_hits.to_numpy()
    b.errorbar(med, yy, xerr=np.vstack([med - low, high - med]), fmt="o", color="#0072B2", capsize=1.5, markersize=3)
    b.scatter(decision.point_first_second_margin_hits, yy, marker="D", s=15, color="#D55E00", zorder=3)
    b.axvline(0, color="#777777", linewidth=0.7)
    b.set(yticks=yy, yticklabels=[], xlabel="First–second margin (hits)")
    b.invert_yaxis()
    b.set_title("b  Winner margin", loc="left", fontweight="bold", pad=3)
    b.spines[["top", "right"]].set_visible(False)
    b.grid(axis="x", color="#D9DDE3", linewidth=0.45)

    med = decision.bootstrap_regret_max_median_hits.to_numpy()
    low = decision.bootstrap_regret_max_ci_low_95_hits.to_numpy()
    high = decision.bootstrap_regret_max_ci_high_95_hits.to_numpy()
    c.errorbar(med, yy, xerr=np.vstack([med - low, high - med]), fmt="o", color="#009E73", capsize=1.5, markersize=3)
    c.scatter(decision.point_mp_selection_regret_max_hits, yy, marker="D", s=15, color="#D55E00", zorder=3)
    c.axvline(0, color="#777777", linewidth=0.7)
    c.set(yticks=yy, yticklabels=[], xlabel="MP-selection regret\n(stable hits per 1000)")
    c.invert_yaxis()
    c.set_title("c  Selection consequence", loc="left", fontweight="bold", pad=3)
    c.spines[["top", "right"]].set_visible(False)
    c.grid(axis="x", color="#D9DDE3", linewidth=0.45)

    top_handles = [Line2D([0], [0], marker="o", color=MODEL_COLORS[m], linewidth=0, markersize=4, label=m) for m in MODEL_ORDER]
    top_handles.append(Line2D([0], [0], color="#555555", linestyle=(0, (2, 2)), linewidth=1, label=r"$K\pi_v$ baseline"))
    bottom_handles = [
        Line2D([0], [0], marker="o", color="#4D4D4D", linewidth=1, markersize=3, label="bootstrap median and 95% interval"),
        Line2D([0], [0], marker="D", color="#D55E00", linewidth=0, markersize=4, label="point estimate"),
    ]
    fig.legend(handles=top_handles, ncol=5, loc="upper center", bbox_to_anchor=(0.53, 0.995), frameon=False, fontsize=5.8, columnspacing=0.9, handlelength=1.7)
    fig.legend(handles=bottom_handles, ncol=2, loc="lower center", bbox_to_anchor=(0.61, -0.12), frameon=False, fontsize=5.8, columnspacing=1.4, handlelength=1.7)
    fig.subplots_adjust(left=0.115, right=0.99, bottom=0.25, top=0.82)
    save(fig, "fig4_revision_model_consequence")


def main() -> None:
    figure2()
    figure3()
    figure4()
    print(json.dumps({"figures": [2, 3, 4], "output": str(FIG.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
