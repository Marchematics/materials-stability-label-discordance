#!/usr/bin/env python3
"""Build the locked main-text figures for referee revision v3."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"
FIG = OUT / "figures"
SRC = OUT / "figure_sources"

MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
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
    ("mp_source_coordinate", "alexmp20_source_coordinate"): "MP vs alex-mp-20",
    ("mp_source_coordinate", "alex_pbe_source_coordinate"): "MP vs Alexandria-PBE",
    ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"): "alex-mp-20 vs Alexandria-PBE",
}
PAIR_COLORS = {
    "MP vs alex-mp-20": "#0072B2",
    "MP vs Alexandria-PBE": "#D55E00",
    "alex-mp-20 vs Alexandria-PBE": "#009E73",
}


def setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            "font.size": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    FIG.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)


def panel_label(axis, label: str) -> None:
    axis.text(-0.08, 1.04, label, transform=axis.transAxes, fontsize=10, fontweight="bold")


def box(axis, xy, width, height, text, face="#F3F5F7", edge="#4C566A", fontsize=7.5):
    patch = FancyBboxPatch(
        xy, width, height, boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=face, edgecolor=edge, linewidth=0.9,
    )
    axis.add_patch(patch)
    axis.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def arrow(axis, start, end):
    axis.add_patch(
        FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="#4C566A")
    )


def figure1() -> None:
    """NMI-style analysis schematic using only the locked referee-v3 estimands."""
    flow = pd.read_csv(OUT / "evaluation" / "physical_support_flow.csv")
    values = dict(zip(flow.stage, flow.n))

    colors = {
        "ink": "#30343B",
        "line": "#70757A",
        "mp": "#3F77A8",
        "mp_light": "#E7F0F8",
        "alexmp": "#4C9B6A",
        "alexmp_light": "#E7F4EB",
        "alexpbe": "#C8753D",
        "alexpbe_light": "#FAEBDD",
        "green": "#2E8B57",
        "green_light": "#E1F3E8",
        "red": "#B85C5C",
        "red_light": "#F8E7E5",
        "gold": "#B8872D",
        "gold_light": "#FFF3D9",
        "grey_light": "#F2F3F4",
    }

    fig, ax = plt.subplots(figsize=(7.35, 4.05))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panels = {
        "a": (0.012, 0.045, 0.316, 0.91),
        "b": (0.342, 0.045, 0.316, 0.91),
        "c": (0.672, 0.045, 0.316, 0.91),
    }

    def xy(panel: str, x: float, y: float) -> tuple[float, float]:
        px, py, pw, ph = panels[panel]
        return px + x * pw, py + y * ph

    def wh(panel: str, w: float, h: float) -> tuple[float, float]:
        _, _, pw, ph = panels[panel]
        return w * pw, h * ph

    def pbox(panel: str, x: float, y: float, w: float, h: float, text: str,
             face: str, edge: str, fontsize: float = 5.8, weight: str = "normal",
             linestyle: str | tuple = "solid", linewidth: float = 0.8) -> None:
        gx, gy = xy(panel, x, y)
        gw, gh = wh(panel, w, h)
        ax.add_patch(FancyBboxPatch(
            (gx, gy), gw, gh,
            boxstyle="round,pad=0.006,rounding_size=0.008",
            facecolor=face, edgecolor=edge, linewidth=linewidth, linestyle=linestyle,
        ))
        ax.text(gx + gw / 2, gy + gh / 2, text, ha="center", va="center",
                fontsize=fontsize, color=colors["ink"], fontweight=weight, linespacing=1.08)

    def parrow(panel: str, start: tuple[float, float], end: tuple[float, float],
               color: str = colors["line"], scale: float = 10, linewidth: float = 0.8) -> None:
        ax.add_patch(FancyArrowPatch(xy(panel, *start), xy(panel, *end),
                                     arrowstyle="-|>", mutation_scale=scale,
                                     linewidth=linewidth, color=color))

    def cylinder(panel: str, x: float, y: float, w: float, h: float,
                 label: str, edge: str, face: str) -> None:
        gx, gy = xy(panel, x, y)
        gw, gh = wh(panel, w, h)
        eh = gh * 0.22
        ax.add_patch(Rectangle((gx, gy + eh / 2), gw, gh - eh,
                               facecolor=face, edgecolor=edge, linewidth=0.9))
        ax.add_patch(Ellipse((gx + gw / 2, gy + gh - eh / 2), gw, eh,
                             facecolor=face, edgecolor=edge, linewidth=0.9))
        ax.add_patch(Ellipse((gx + gw / 2, gy + eh / 2), gw, eh,
                             facecolor=face, edgecolor=edge, linewidth=0.9, alpha=0.85))
        ax.text(gx + gw / 2, gy + gh * 0.66, label, ha="center", va="center",
                fontsize=5.2, color=edge, fontweight="bold", linespacing=1.0)
        pts = np.array([[0.22, 0.28], [0.42, 0.40], [0.68, 0.31], [0.31, 0.58], [0.60, 0.62], [0.78, 0.50]])
        for i, j in [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5), (2, 5)]:
            ax.plot(gx + pts[[i, j], 0] * gw, gy + pts[[i, j], 1] * gh,
                    color=edge, linewidth=0.45, alpha=0.65)
        ax.scatter(gx + pts[:, 0] * gw, gy + pts[:, 1] * gh,
                   s=8, color=edge, edgecolors="white", linewidths=0.2, zorder=4)

    for label, (px, py, pw, ph) in panels.items():
        ax.add_patch(FancyBboxPatch(
            (px, py), pw, ph,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="white", edgecolor=colors["line"], linewidth=0.7,
        ))
        ax.text(px + 0.020 * pw, py + 0.958 * ph, label,
                fontsize=11, fontweight="bold", ha="left", va="center")

    # a | Frozen multi-source cohort.
    ax.text(*xy("a", 0.54, 0.955), "Frozen multi-source cohort",
            ha="center", va="center", fontsize=7.2, fontweight="bold")
    cylinder("a", 0.045, 0.675, 0.29, 0.17, "Materials\nProject", colors["mp"], colors["mp_light"])
    cylinder("a", 0.045, 0.445, 0.29, 0.17, "MatterGen\nalex-mp-20", colors["alexmp"], colors["alexmp_light"])
    cylinder("a", 0.045, 0.215, 0.29, 0.17, "Official\nAlexandria-PBE", colors["alexpbe"], colors["alexpbe_light"])
    for yy, cc in [(0.760, colors["mp"]), (0.530, colors["alexmp"]), (0.300, colors["alexpbe"])]:
        ax.plot(*zip(xy("a", 0.335, yy), xy("a", 0.440, yy)), color=cc,
                linewidth=4.0, alpha=0.38, solid_capstyle="round")

    funnel = [xy("a", 0.43, 0.835), xy("a", 0.94, 0.835), xy("a", 0.82, 0.285),
              xy("a", 0.75, 0.255), xy("a", 0.75, 0.175), xy("a", 0.62, 0.175),
              xy("a", 0.62, 0.255), xy("a", 0.55, 0.285)]
    ax.add_patch(Polygon(funnel, closed=True, facecolor="#FAFAFA",
                         edgecolor=colors["line"], linewidth=0.9))
    for yy in (0.675, 0.515, 0.365):
        ax.plot([xy("a", 0.48, yy)[0], xy("a", 0.89, yy)[0]],
                [xy("a", 0, yy)[1], xy("a", 0, yy)[1]],
                color="#A0A4A8", linewidth=0.5, linestyle=(0, (2, 2)))
    ax.text(*xy("a", 0.685, 0.755), "D2 matched cohort\n36,802",
            ha="center", va="center", fontsize=5.8, fontweight="bold")
    ax.text(*xy("a", 0.685, 0.595), "D5 four-score intersection\n36,801",
            ha="center", va="center", fontsize=5.5)
    ax.text(*xy("a", 0.685, 0.435), "compound candidates\n36,681",
            ha="center", va="center", fontsize=5.5)
    ax.text(*xy("a", 0.685, 0.315), "five-coordinate complete\n36,650",
            ha="center", va="center", fontsize=5.4, color=colors["green"], fontweight="bold")
    parrow("a", (0.685, 0.175), (0.685, 0.115), scale=11)
    pbox("a", 0.48, 0.055, 0.41, 0.075, r"$M_{\mathrm{phys}}=36{,}650$",
         colors["green_light"], colors["green"], fontsize=6.7, weight="bold")
    ax.text(*xy("a", 0.50, 0.015), "120 elemental targets: reference information only",
            ha="center", va="center", fontsize=4.3, color="#666666")

    # b | Five physical coordinates; policies kept separate.
    ax.text(*xy("b", 0.54, 0.955), "Physical endpoint layer",
            ha="center", va="center", fontsize=7.2, fontweight="bold")
    ax.text(*xy("b", 0.50, 0.865), "source coordinates",
            ha="center", va="center", fontsize=5.1, color="#666666")
    pbox("b", 0.055, 0.705, 0.27, 0.115, "MP\nnative", colors["mp_light"], colors["mp"], fontsize=5.5, weight="bold")
    pbox("b", 0.365, 0.705, 0.27, 0.115, "alex-mp-20\nnative", colors["alexmp_light"], colors["alexmp"], fontsize=5.2, weight="bold")
    pbox("b", 0.675, 0.705, 0.27, 0.115, "Alexandria-PBE\nnative", colors["alexpbe_light"], colors["alexpbe"], fontsize=4.6, weight="bold")
    pbox("b", 0.235, 0.505, 0.53, 0.095, "frozen matched D2 phase inventory",
         colors["gold_light"], colors["gold"], fontsize=5.4)
    for xx, cc in [(0.19, colors["mp"]), (0.50, colors["alexmp"]), (0.81, colors["alexpbe"])]:
        parrow("b", (xx, 0.705), (0.50, 0.600), color=cc, scale=8, linewidth=0.65)
    pbox("b", 0.10, 0.315, 0.35, 0.105, "MP\nmatched pool", colors["mp_light"], colors["mp"], fontsize=5.5, weight="bold")
    pbox("b", 0.55, 0.315, 0.35, 0.105, "Alexandria-PBE\nmatched pool", colors["alexpbe_light"], colors["alexpbe"], fontsize=5.1, weight="bold")
    parrow("b", (0.42, 0.505), (0.275, 0.420), color=colors["mp"], scale=8, linewidth=0.65)
    parrow("b", (0.58, 0.505), (0.725, 0.420), color=colors["alexpbe"], scale=8, linewidth=0.65)
    pbox("b", 0.18, 0.165, 0.64, 0.075, "five physical coordinates\none frozen ranking per model",
         colors["green_light"], colors["green"], fontsize=5.1, weight="bold")
    pbox("b", 0.10, 0.045, 0.80, 0.070, "agreement · consensus · audit  |  derived policies",
         colors["grey_light"], "#8A8D91", fontsize=4.9, linestyle=(0, (3, 2)))
    ax.text(*xy("b", 0.50, 0.132), "policies excluded from the physical-endpoint comparison",
            ha="center", va="center", fontsize=4.0, color="#6B6B6B")

    # c | Equivalence-class-excluded batch-relative ranking.
    ax.text(*xy("c", 0.54, 0.955), "Self-exclusion-aware ranking",
            ha="center", va="center", fontsize=7.2, fontweight="bold")
    pbox("c", 0.055, 0.735, 0.40, 0.105, "frozen D5\ncandidate batch", colors["mp_light"], colors["mp"], fontsize=5.5, weight="bold")
    # Candidate/equivalence-class cluster.
    gx, gy = xy("c", 0.60, 0.790)
    ax.scatter([gx, gx + 0.030, gx + 0.015], [gy, gy + 0.018, gy - 0.025],
               s=[24, 13, 13], color=[colors["red"], "#D9A0A0", "#D9A0A0"],
               edgecolors="white", linewidths=0.35, zorder=5)
    ax.add_patch(Ellipse((gx + 0.015, gy - 0.002), 0.090, 0.095,
                         facecolor=colors["red_light"], edgecolor=colors["red"],
                         linewidth=0.8, linestyle=(0, (3, 2)), zorder=2))
    ax.text(*xy("c", 0.820, 0.790), "target's full\nequivalence class",
            ha="center", va="center", fontsize=4.2, color=colors["red"])
    parrow("c", (0.50, 0.700), (0.50, 0.620), scale=10)
    pbox("c", 0.12, 0.515, 0.76, 0.105, "remove the target class before every hull",
         colors["red_light"], colors["red"], fontsize=5.0, weight="bold")
    parrow("c", (0.50, 0.515), (0.50, 0.455), scale=10)

    # Schematic reference hull and signed margin.
    hx, hy = xy("c", 0.10, 0.205)
    hw, hh = wh("c", 0.80, 0.235)
    curve_x = np.array([0.05, 0.23, 0.42, 0.62, 0.82, 0.95])
    curve_y = np.array([0.82, 0.42, 0.29, 0.36, 0.55, 0.88])
    ax.plot(hx + curve_x * hw, hy + curve_y * hh, color=colors["ink"], linewidth=1.0)
    ax.scatter(hx + curve_x * hw, hy + curve_y * hh, s=13, color="#7A7F85", zorder=3)
    tx = 0.53
    hull_y = np.interp(tx, curve_x, curve_y)
    target_y = hull_y - 0.20
    ax.scatter([hx + tx * hw], [hy + target_y * hh], s=28, color=colors["green"],
               edgecolors="white", linewidths=0.4, zorder=5)
    ax.plot([hx + tx * hw, hx + tx * hw], [hy + target_y * hh, hy + hull_y * hh],
            color=colors["green"], linewidth=1.0, linestyle=(0, (3, 2)))
    ax.text(hx + (tx + 0.04) * hw, hy + (target_y + 0.08) * hh,
            "signed margin", fontsize=4.8, color=colors["green"], va="center")
    ax.text(*xy("c", 0.50, 0.465), "reference hull: remaining batch phases + elemental anchors",
            ha="center", va="center", fontsize=4.6, color="#555555")
    pbox("c", 0.12, 0.065, 0.76, 0.075, "36,681 candidates × 4 models\n146,724 audited scores",
         colors["green_light"], colors["green"], fontsize=4.9, weight="bold")
    ax.text(*xy("c", 0.50, 0.018), "retrospective · batch-relative · transductive",
            ha="center", va="center", fontsize=4.8, fontweight="bold", color=colors["ink"])

    fig.savefig(FIG / "fig1_revision_analysis_object.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig1_revision_analysis_object.svg", bbox_inches="tight")
    fig.savefig(FIG / "fig1_revision_analysis_object.png", dpi=450, bbox_inches="tight")
    fig.savefig(FIG / "fig1_revision_analysis_object.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)

    pd.DataFrame([
        {"stage": "D2 matched cohort", "n": 36_802},
        {"stage": "D5 four-score intersection", "n": 36_801},
        {"stage": "D5 compound candidate universe", "n": int(values["D5 compound candidate universe"])},
        {"stage": "Mphys fixed physical evaluation support", "n": int(values["Mphys fixed physical evaluation support"])},
        {"stage": "elemental targets excluded from candidate ranking", "n": 120},
        {"stage": "primary candidate-model exclusion audits", "n": 146_724},
    ]).to_csv(SRC / "fig1_cohort_flow.csv", index=False)
    pd.DataFrame([
        {"layer": "physical", "endpoint": key, "label": ENDPOINT_LABELS[key]}
        for key in ENDPOINT_LABELS
    ] + [
        {"layer": "derived_policy", "endpoint": "agreement", "label": "agreement filter"},
        {"layer": "derived_policy", "endpoint": "consensus", "label": "consensus selection"},
        {"layer": "derived_policy", "endpoint": "audit", "label": "audit policy"},
    ]).to_csv(SRC / "fig1_endpoint_layer.csv", index=False)
    pd.DataFrame([
        {"property": "estimand", "value": "leave-one-tolerance-equivalence-class-out batch-relative transductive signed reference-hull margin"},
        {"property": "compound_candidate_n", "value": 36_681},
        {"property": "model_n", "value": 4},
        {"property": "candidate_model_audit_n", "value": 146_724},
        {"property": "decomposition_simplex_overlap_n", "value": 0},
    ]).to_csv(SRC / "fig1_ranking_construction.csv", index=False)

def figure2() -> None:
    point = pd.read_csv(OUT / "evaluation" / "endpoint_threshold_scan.csv")
    point = point[
        point.support.eq("D2_native_full") & point.threshold_meV_per_atom.isin([0, 10, 25, 50])
    ].copy()
    boot = pd.read_csv(OUT / "bootstrap_conflicts" / "endpoint_threshold_cluster_bootstrap.csv")
    boot = boot[
        boot.support.eq("D2_native_full") & boot.threshold_meV_per_atom.isin([0, 10, 25, 50])
    ]
    scan = point.merge(
        boot,
        on=["support", "threshold_meV_per_atom", "endpoint_a", "endpoint_b"],
        validate="one_to_one",
    )
    scan["pair"] = [PAIR_LABELS[(a, b)] for a, b in zip(scan.endpoint_a, scan.endpoint_b)]
    scan.to_csv(SRC / "fig2_threshold_scan.csv", index=False)

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
    ind.to_csv(SRC / "fig2_indeterminate_scan.csv", index=False)

    # A single horizontal row reads cleanly in the journal's double-column
    # format.  Legends occupy dedicated space above each axes so they never
    # cover data, uncertainty bands, axis labels, or annotations.
    fig = plt.figure(figsize=(7.35, 2.72))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.07, 1.0, 1.0], wspace=0.66)
    a = fig.add_subplot(grid[0, 0])
    b = fig.add_subplot(grid[0, 1])
    c = fig.add_subplot(grid[0, 2])
    for pair, group in scan.groupby("pair"):
        group = group.sort_values("threshold_meV_per_atom")
        x = group.threshold_meV_per_atom.to_numpy()
        a.plot(x, 100 * group.switch_rate, marker="o", markersize=3, linewidth=1.4, label=pair, color=PAIR_COLORS[pair])
        a.fill_between(x, 100 * group.switch_rate_ci_low_95, 100 * group.switch_rate_ci_high_95, color=PAIR_COLORS[pair], alpha=0.14, linewidth=0)
    a.set_xlabel("Threshold (meV atom$^{-1}$)")
    a.set_ylabel("Endpoint-switch rate (%)")
    a.set_xticks([0, 10, 25, 50])
    a.set_ylim(5, 17)
    a.legend(
        fontsize=5.4,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.03),
        borderaxespad=0,
        frameon=False,
        title="a  Threshold scan",
        title_fontproperties={"size": 7.2, "weight": "bold"},
        handlelength=2.0,
        labelspacing=0.22,
    )

    x = ind.indeterminate_width_meV_per_atom.to_numpy()
    b.bar(x, ind.robust_conflict_n, width=4.5, color="#D55E00", alpha=0.82, label="Robust conflicts")
    b.set_xlabel("Width (meV atom$^{-1}$)")
    b.set_ylabel("Robust conflict count", color="#A44200")
    b.tick_params(axis="y", labelcolor="#A44200")
    b.set_xticks([10, 30, 50])
    b2 = b.twinx()
    b2.plot(x, ind.decisive_n, color="#0072B2", marker="o", markersize=3, linewidth=1.4, label="Decisive support")
    b2.tick_params(axis="y", labelcolor="#0072B2")
    b_handles, b_labels = b.get_legend_handles_labels()
    b2_handles, b2_labels = b2.get_legend_handles_labels()
    b.legend(
        b_handles + b2_handles,
        b_labels + b2_labels,
        fontsize=5.4,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.03),
        borderaxespad=0,
        frameon=False,
        title="b  MP–Alexandria counts",
        title_fontproperties={"size": 7.2, "weight": "bold"},
        handlelength=1.8,
        labelspacing=0.22,
    )

    for column, label, color in (
        ("robust_conflict_rate_full_support", "All reconstructable rows", "#D55E00"),
        ("robust_conflict_rate_decisive_support", "Decisive rows", "#0072B2"),
    ):
        c.plot(x, 100 * ind[column], marker="o", markersize=3, linewidth=1.4, label=label, color=color)
        c.fill_between(
            x,
            100 * ind[f"{column}_ci_low_95"],
            100 * ind[f"{column}_ci_high_95"],
            color=color, alpha=0.14, linewidth=0,
        )
    c.set_xlabel("Width (meV atom$^{-1}$)")
    c.set_ylabel("Robust-conflict rate (%)")
    c.set_xticks([10, 30, 50])
    c.legend(
        fontsize=5.4,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.03),
        borderaxespad=0,
        frameon=False,
        title="c  MP–Alexandria rates",
        title_fontproperties={"size": 7.2, "weight": "bold"},
        handlelength=2.0,
        labelspacing=0.22,
    )
    fig.savefig(FIG / "fig2_revision_threshold_robustness.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig2_revision_threshold_robustness.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig2_revision_threshold_robustness.png", dpi=450, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig2_revision_threshold_robustness.tiff", dpi=600, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def figure3() -> None:
    data = pd.read_csv(OUT / "evaluation" / "common_pool_decomposition_threshold_scan.csv")
    data = data[data.support.eq("D2") & data.threshold_meV_per_atom.isin([0, 10, 25, 50])].copy()
    data.to_csv(SRC / "fig3_common_pool_threshold_decomposition.csv", index=False)
    thresholds = data.threshold_meV_per_atom.to_numpy()
    # Horizontal paired bars preserve the two distinct totals while remaining
    # legible at one-column width.
    positions = np.arange(len(data) * 2, dtype=float)
    positions[2:] += 0.45
    positions[4:] += 0.45
    positions[6:] += 0.45
    native_y = positions[0::2]
    common_y = positions[1::2]
    height = 0.72
    fig, axis = plt.subplots(figsize=(3.35, 3.75))
    native_components = [
        ("phase_pool_sensitive_n", "Phase-pool-sensitive", "#56B4E9"),
        ("persistent_conflict_n", "Persistent", "#D55E00"),
        ("unreconstructable_native_conflict_n", "Unreconstructable", "#999999"),
    ]
    common_components = [
        ("persistent_conflict_n", "Persistent", "#D55E00"),
        ("hidden_common_pool_conflict_n", "Hidden matched-pool", "#CC79A7"),
    ]
    left = np.zeros(len(data))
    for column, label, color in native_components:
        axis.barh(native_y, data[column], height, left=left, color=color, label=label)
        left += data[column].to_numpy()
    left = np.zeros(len(data))
    for column, label, color in common_components:
        axis.barh(common_y, data[column], height, left=left, color=color, label=label if label not in [x[1] for x in native_components] else None)
        left += data[column].to_numpy()
    for index, row in enumerate(data.itertuples()):
        axis.text(row.all_native_conflict_n + 90, native_y[index], f"{int(row.all_native_conflict_n):,}", va="center", fontsize=6.2)
        axis.text(row.common_pool_conflict_n + 90, common_y[index], f"{int(row.common_pool_conflict_n):,}", va="center", fontsize=6.2)
    tick_positions = np.ravel(np.column_stack([native_y, common_y]))
    tick_labels = []
    for value in thresholds:
        tick_labels.extend([f"{int(value)} meV · Native", f"{int(value)} meV · Matched"])
    axis.set_yticks(tick_positions, tick_labels)
    axis.invert_yaxis()
    axis.set_xlabel("Conflict rows")
    axis.set_xlim(0, max(data.all_native_conflict_n.max(), data.common_pool_conflict_n.max()) * 1.17)
    handles, labels = axis.get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    axis.legend(
        dedup.values(),
        dedup.keys(),
        ncol=2,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.02),
        borderaxespad=0,
        fontsize=6.0,
        frameon=False,
        columnspacing=0.9,
        handlelength=1.7,
    )
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="x", color="#D9DDE3", linewidth=0.5, zorder=0)
    axis.set_axisbelow(True)
    fig.savefig(FIG / "fig3_revision_common_pool_decomposition.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig3_revision_common_pool_decomposition.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig3_revision_common_pool_decomposition.png", dpi=450, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig3_revision_common_pool_decomposition.tiff", dpi=600, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def figure4() -> None:
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
    budget = budget[budget.threshold_meV_per_atom.eq(0) & budget.K.eq(1000)].copy()
    decision = budget.drop_duplicates("coordinate_endpoint").copy()
    decision["endpoint_order"] = decision.coordinate_endpoint.map({value: i for i, value in enumerate(order)})
    decision = decision.sort_values("endpoint_order")
    decision.to_csv(SRC / "fig4_margin_regret.csv", index=False)

    fig = plt.figure(figsize=(7.35, 4.45))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.18, 1], hspace=0.55, wspace=0.48)
    a = fig.add_subplot(grid[0, :])
    b = fig.add_subplot(grid[1, 0])
    c = fig.add_subplot(grid[1, 1])
    x = np.arange(len(order))
    width = 0.18
    for model_index, model in enumerate(MODELS):
        group = topk[topk.model_name.eq(model)].set_index("coordinate_endpoint").loc[order]
        xpos = x + (model_index - 1.5) * width
        y = group.expected_stable_hits.to_numpy()
        lower = y - group.bootstrap_ci_low_95.to_numpy()
        upper = group.bootstrap_ci_high_95.to_numpy() - y
        a.bar(xpos, y, width, color=MODEL_COLORS[model], label=model, zorder=2)
        a.errorbar(xpos, y, yerr=np.vstack([lower, upper]), fmt="none", ecolor="#333333", elinewidth=0.6, capsize=1.5, zorder=3)
    baseline = topk.drop_duplicates("coordinate_endpoint").set_index("coordinate_endpoint").loc[order]
    for index, value in enumerate(baseline.random_expected_hits):
        a.hlines(value, index - 0.43, index + 0.43, colors="#555555", linestyles="--", linewidth=0.8)
    a.set_xticks(x, [ENDPOINT_LABELS[value].replace(" ", "\n", 1) for value in order], rotation=0)
    a.set_ylabel("Stable hits at $K=1000$")
    a.legend(
        ncol=4,
        fontsize=6.5,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        borderaxespad=0,
        frameon=False,
        title="a  Absolute validation yield",
        title_fontproperties={"size": 9.0, "weight": "bold"},
        columnspacing=1.2,
        handlelength=1.8,
    )

    panel_label(b, "b")
    y = np.arange(len(order))
    med = decision.first_second_margin_median_hits.to_numpy()
    low = decision.first_second_margin_ci_low_95_hits.to_numpy()
    high = decision.first_second_margin_ci_high_95_hits.to_numpy()
    b.errorbar(med, y, xerr=np.vstack([med - low, high - med]), fmt="o", color="#0072B2", capsize=2, markersize=3)
    b.scatter(decision.point_first_second_margin_hits, y, marker="D", s=16, color="#D55E00", label="Point estimate", zorder=3)
    for index, record in enumerate(decision.itertuples()):
        winners = ", ".join(json.loads(record.point_winner_models_json))
        b.text(max(high[index], record.point_first_second_margin_hits) + 0.6, index, winners, va="center", fontsize=6.2)
    b.axvline(0, color="#777777", linewidth=0.7)
    b.set_yticks(y, [ENDPOINT_LABELS[value] for value in order])
    b.invert_yaxis()
    b.set_xlabel("First–second margin (hits)")
    b.set_title("Winner margins", fontsize=9)

    panel_label(c, "c")
    med = decision.bootstrap_regret_max_median_hits.to_numpy()
    low = decision.bootstrap_regret_max_ci_low_95_hits.to_numpy()
    high = decision.bootstrap_regret_max_ci_high_95_hits.to_numpy()
    c.errorbar(med, y, xerr=np.vstack([med - low, high - med]), fmt="o", color="#009E73", capsize=2, markersize=3, label="Bootstrap median")
    c.scatter(decision.point_mp_selection_regret_max_hits, y, marker="D", s=16, color="#D55E00", label="Point estimate", zorder=3)
    c.axvline(0, color="#777777", linewidth=0.7)
    c.set_yticks(y, [])
    c.invert_yaxis()
    c.set_xlabel("MP-selection regret\n(stable hits per 1000)")
    c.set_title("Selection consequence", fontsize=9)
    # Panels b and c share the same mark semantics.  A figure-level key below
    # the panels removes the two legends that previously obscured intervals.
    decision_handles = [
        Line2D([0], [0], marker="o", color="#4D4D4D", linewidth=1.2, markersize=3, label="Bootstrap median and 95% interval"),
        Line2D([0], [0], marker="D", color="#D55E00", linewidth=0, markersize=4, label="Point estimate"),
    ]
    fig.legend(
        handles=decision_handles,
        ncol=2,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.015),
        frameon=False,
        fontsize=6.4,
        columnspacing=1.4,
        handlelength=2.0,
    )
    fig.subplots_adjust(bottom=0.17)
    fig.savefig(FIG / "fig4_revision_model_consequence.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig4_revision_model_consequence.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig4_revision_model_consequence.png", dpi=450, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(FIG / "fig4_revision_model_consequence.tiff", dpi=600, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def main() -> None:
    setup()
    figure1()
    figure2()
    figure3()
    figure4()
    print(json.dumps({"figures": 4, "output": str(FIG.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
