#!/usr/bin/env python3
"""Build manuscript figures from the repaired common-support model analysis.

The script deliberately reads only the repaired model-evaluation outputs.  It
does not recover values from the earlier D5/six-view score analysis.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "outputs" / "repaired_model_evaluation_v1"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
VIEWS = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view")
DISCOVERY_VIEWS = ("mp_native", "common_pool", "audit_view")
COLORS = {"ALIGNN-FF": "#5B6FEA", "CHGNet": "#D968A5", "M3GNet": "#E7A933", "MACE-MP": "#83C95A"}
MARKERS = {"ALIGNN-FF": "o", "CHGNet": "s", "M3GNet": "^", "MACE-MP": "D"}
STYLES = {"mp_native": (0, (5, 2)), "common_pool": "solid", "audit_view": (0, (1.2, 1.8))}
VIEW_LABELS = {"mp_native": "MP-native", "alexmp20_native": "alex-mp-20", "alex_pbe_native": "Alexandria-PBE", "common_pool": "Common pool", "audit_view": "Audit view"}
METRICS = ("f1_fixed_threshold", "auroc", "auprc", "stable_yield_at_1000")
METRIC_LABELS = {"f1_fixed_threshold": "F1", "auroc": "AUROC", "auprc": "AUPRC", "stable_yield_at_1000": "Stable yield@1k"}
CM = 1 / 2.54


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.2, "axes.titlesize": 9.4,
        "axes.labelsize": 8.0, "axes.linewidth": 0.65, "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0, "legend.fontsize": 6.8, "pdf.fonttype": 42,
        "ps.fonttype": 42, "savefig.facecolor": "white", "axes.facecolor": "white",
    })


def clean(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D9DDE3", linewidth=0.55, zorder=0)
    ax.tick_params(length=3.0, width=0.6, color="#4A5058")


def save(fig: plt.Figure, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(out / f"{name}.tiff", dpi=600, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig1(curves: pd.DataFrame, source: Path, out: Path) -> None:
    source.mkdir(parents=True, exist_ok=True)
    curves.to_csv(source / "fig1_repaired_exact_discovery_curves.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(17.1 * CM, 6.4 * CM), gridspec_kw={"wspace": 0.32})
    for ax, value, ylabel, letter in zip(axes, ("stable_yield", "recall"), ("Stable yield@K", "Recall of view-defined stable set"), ("a", "b")):
        for model in MODELS:
            for view in DISCOVERY_VIEWS:
                d = curves[(curves.model_name.eq(model)) & (curves.label_view.eq(view))]
                ax.plot(d["rank"], d[value], color=COLORS[model], linestyle=STYLES[view], linewidth=1.45, alpha=0.98)
        ax.axvline(1000, color="#7A8390", linewidth=0.7, linestyle=(0, (4, 3)), zorder=1)
        ax.text(1000, 0.025 if value == "recall" else 0.03, "1,000", rotation=90, ha="right", va="bottom", fontsize=6.3, color="#65707D")
        ax.set_xlim(1, 10000)
        ax.set_xticks([0, 2500, 5000, 7500, 10000], ["0", "2.5k", "5k", "7.5k", "10k"])
        ax.set_xlabel("Candidates validated, K")
        ax.set_ylabel(ylabel)
        ax.set_title("Discovery yield" if value == "stable_yield" else "Recovery", pad=4)
        clean(ax)
        ax.text(-0.14, 1.04, letter, transform=ax.transAxes, fontweight="bold", fontsize=9.5)
    axes[0].set_ylim(0.35, 0.95)
    axes[1].set_ylim(0, 0.72)
    model_handles = [Line2D([0], [0], color=COLORS[m], lw=2.2, label=m) for m in MODELS]
    view_handles = [Line2D([0], [0], color="#42484F", lw=1.6, linestyle=STYLES[v], label=VIEW_LABELS[v]) for v in DISCOVERY_VIEWS]
    fig.legend(model_handles + view_handles, [h.get_label() for h in model_handles + view_handles], ncol=4, loc="lower center", bbox_to_anchor=(0.50, -0.11), columnspacing=1.15, handlelength=2.0)
    fig.subplots_adjust(bottom=0.24, left=0.08, right=0.99, top=0.91)
    save(fig, out, "fig1_sourceaware_discovery_curves")


def dominant_tables(metrics: pd.DataFrame, topk: pd.DataFrame, bands: pd.DataFrame, band_ci: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    point = metrics.melt(id_vars=["model_name", "label_view"], value_vars=["f1_fixed_threshold", "auroc", "auprc"], var_name="metric", value_name="value")
    y = topk[topk.K.eq(1000)][["model_name", "label_view", "stable_yield_at_k"]].rename(columns={"stable_yield_at_k": "value"})
    y["metric"] = "stable_yield_at_1000"
    point = pd.concat([point, y], ignore_index=True)
    label_bands = bands[bands.scope.eq("label_view_band")][["model_name", "metric", "spread"]].rename(columns={"spread": "label_view_band"})
    margin = bands[bands.scope.eq("between_model_spread")].groupby("metric", as_index=False).spread.median().rename(columns={"spread": "median_between_model_margin"})
    dominance = label_bands.merge(margin, on="metric").merge(band_ci[["model_name", "metric", "ci_low_95", "ci_high_95"]], on=["model_name", "metric"], how="left")
    dominance = dominance[dominance.metric.isin(METRICS)].copy()
    dominance["uncertainty_dominance_ratio"] = dominance.label_view_band / dominance.median_between_model_margin
    dominance["ratio_ci_low_95"] = dominance.ci_low_95 / dominance.median_between_model_margin
    dominance["ratio_ci_high_95"] = dominance.ci_high_95 / dominance.median_between_model_margin
    ranks = point[point.metric.eq("f1_fixed_threshold")].copy()
    ranks["rank"] = ranks.groupby("label_view").value.rank(method="min", ascending=False).astype(int)
    return dominance, ranks, point


def fig4(metrics: pd.DataFrame, topk: pd.DataFrame, bands: pd.DataFrame, band_ci: pd.DataFrame, deltas: pd.DataFrame, winners: pd.DataFrame, source: Path, out: Path) -> None:
    dominance, ranks, point = dominant_tables(metrics, topk, bands, band_ci)
    for filename, table in {"fig4_repaired_uncertainty_dominance.csv": dominance, "fig4_repaired_f1_ranks.csv": ranks, "fig4_repaired_point_metrics.csv": point, "fig4_paired_label_differences.csv": deltas, "fig4_model_winner_probabilities.csv": winners}.items():
        table.to_csv(source / filename, index=False)
    fig = plt.figure(figsize=(17.1 * CM, 10.6 * CM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.02, 1], hspace=0.52, wspace=0.38)
    axa = fig.add_subplot(gs[0, :]); axb = fig.add_subplot(gs[1, 0]); axc = fig.add_subplot(gs[1, 1])
    xloc = {m: i for i, m in enumerate(METRICS)}
    offsets = np.linspace(-0.21, 0.21, len(MODELS))
    for offset, model in zip(offsets, MODELS):
        d = dominance[dominance.model_name.eq(model)].set_index("metric").reindex(METRICS)
        x = np.array([xloc[m] + offset for m in METRICS])
        lower = np.maximum(0.0, d.uncertainty_dominance_ratio - d.ratio_ci_low_95)
        upper = np.maximum(0.0, d.ratio_ci_high_95 - d.uncertainty_dominance_ratio)
        axa.errorbar(x, d.uncertainty_dominance_ratio, yerr=np.vstack([lower, upper]), fmt=MARKERS[model], color=COLORS[model], ms=4.4, capsize=2, elinewidth=0.75, markeredgecolor="white", markeredgewidth=0.45, label=model, zorder=3)
    axa.axhline(1, color="#8F4B45", linestyle=(0, (4, 3)), linewidth=0.85)
    axa.text(3.43, 1.07, "equal variation", ha="right", va="bottom", fontsize=6.4, color="#8F4B45")
    axa.set_yscale("log"); axa.set_ylim(0.45, 6.5); axa.set_yticks([0.5, 1, 2, 4], ["0.5", "1", "2", "4"])
    axa.set_xticks(range(len(METRICS)), [METRIC_LABELS[m] for m in METRICS]); axa.set_ylabel("Label-view band / median model margin")
    axa.set_title("Label-view variation relative to model margins", pad=4)
    clean(axa); axa.legend(ncol=4, loc="upper left", frameon=False, columnspacing=1.0, handletextpad=0.35)
    axa.text(-0.035, 1.04, "a", transform=axa.transAxes, fontweight="bold", fontsize=9.5)

    x = np.arange(len(VIEWS))
    for model in MODELS:
        d = ranks[ranks.model_name.eq(model)].set_index("label_view").reindex(VIEWS)
        axb.plot(x, d["rank"], color=COLORS[model], marker=MARKERS[model], linewidth=1.55, ms=3.6, label=model)
    axb.set_xticks(x, ["MP", "alex-mp-20", "Alex-PBE", "Common", "Audit"], rotation=18, ha="right")
    axb.set_yticks([1, 2, 3, 4]); axb.set_ylim(4.35, 0.65); axb.set_ylabel("F1 rank")
    axb.set_title("Real-model rank across fixed-support views", pad=4); clean(axb); axb.text(-0.16, 1.04, "b", transform=axb.transAxes, fontweight="bold", fontsize=9.5)

    for metric in METRICS:
        d = dominance[dominance.metric.eq(metric)]
        axc.scatter(d.median_between_model_margin, d.label_view_band, s=28, color=[COLORS[m] for m in d.model_name], edgecolor="white", linewidth=0.45, zorder=3)
        axc.annotate(METRIC_LABELS[metric], (d.median_between_model_margin.median(), d.label_view_band.median()), xytext=(4, 4), textcoords="offset points", fontsize=6.0, color="#323840")
    low, high = 0.04, 0.40
    axc.plot([low, high], [low, high], color="#8F4B45", linestyle=(0, (4, 3)), linewidth=0.85)
    axc.set_xlim(low, high); axc.set_ylim(low, high); axc.set_xlabel("Median model margin"); axc.set_ylabel("Label-view band")
    axc.set_title("Absolute variation", pad=4); clean(axc); axc.text(-0.16, 1.04, "c", transform=axc.transAxes, fontweight="bold", fontsize=9.5)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.95, bottom=0.10)
    save(fig, out, "fig4_model_rank_audit")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT)
    p.add_argument("--out", type=Path, default=DEFAULT / "manuscript_figures")
    p.add_argument("--manuscript-figures", type=Path)
    a = p.parse_args()
    style()
    source = a.input / "figure_source_data"
    curves = pd.read_parquet(a.input / "exact_discovery_curves_fixed_support.parquet")
    metrics = pd.read_csv(a.input / "metrics_fixed_support.csv")
    topk = pd.read_csv(a.input / "topk_fixed_support.csv")
    bands = pd.read_csv(a.input / "band_and_model_spread_fixed_support.csv")
    band_ci = pd.read_csv(a.input / "label_bands_cluster_bootstrap.csv")
    deltas = pd.read_csv(a.input / "paired_label_view_differences_cluster_bootstrap.csv")
    winners = pd.read_csv(a.input / "model_winner_probabilities_cluster_bootstrap.csv")
    fig1(curves, source, a.out)
    fig4(metrics, topk, bands, band_ci, deltas, winners, source, a.out)
    if a.manuscript_figures:
        a.manuscript_figures.mkdir(parents=True, exist_ok=True)
        for name in ("fig1_sourceaware_discovery_curves", "fig4_model_rank_audit"):
            for ext in ("pdf", "tiff"):
                shutil.copy2(a.out / f"{name}.{ext}", a.manuscript_figures / f"{name}.{ext}")


if __name__ == "__main__":
    main()
