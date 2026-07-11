#!/usr/bin/env python3
"""Build Digital Discovery submission figures from frozen Phase 1/2 rows.

All curves are row-level cumulative calculations. No spline interpolation is
used. NMI-upgrade/referee scaffold outputs are outside this script's inputs.

Figure 1/2 use the presentation grammar of the MIT-licensed Matbench Discovery
v1.1.0 plotting scripts retained under ``third_party/``: Light24 colours,
line-dash identities, a marginal density panel, external legends and an explicit
rolling-window scale bar. This is a style reference only; numerical results are
calculated from frozen SourceAware outputs below.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, LogLocator
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sourceaware.dd_submission import (
    DEFAULT_OUT,
    DEFAULT_PHASE1,
    DEFAULT_PHASE2,
    DISCOVERY_LABEL_VIEWS,
    PRIMARY_METRICS,
    REAL_MODELS,
    candidate_claim_tables,
    conflict_decomposition,
    denominator_summary,
    ensure_dir,
    exact_discovery_curves,
    exact_primary_metrics,
    pairwise_native_conflicts,
    rank_flip_normalisation,
    rolling_conflict_table,
    uncertainty_dominance_tables,
    write_claims_outputs,
)


CM = 1 / 2.54
MODEL_COLORS = {
    # Plotly Light24 entries used in the Matbench Discovery NMI reference figure.
    "ALIGNN-FF": "#636EFA",
    "CHGNet": "#FF97FF",
    "M3GNet": "#FECB52",
    "MACE-MP": "#B6E880",
}
MODEL_MARKERS = {"ALIGNN-FF": "o", "CHGNet": "s", "M3GNet": "^", "MACE-MP": "D"}
MODEL_LINESTYLES = {
    "ALIGNN-FF": (0, (5.5, 1.7, 1.1, 1.7)),
    "CHGNet": (0, (5.5, 2.6)),
    "M3GNet": (0, (9.0, 2.8)),
    "MACE-MP": (0, (1.25, 1.55)),
}
VIEW_STYLES = {"mp_native": (0, (5, 2)), "consensus": (0, (1.2, 1.5)), "audit_view": "-"}
VIEW_LABELS = {"mp_native": "MP-native", "consensus": "Consensus", "audit_view": "Audit view"}
PAIR_COLORS = {
    "MP vs official Alexandria-PBE": "#19D3F3",
    "alex-mp-20 vs official Alexandria-PBE": "#F08A3C",
    "MP vs alex-mp-20": "#00CC96",
}
PAIR_STYLES = {
    "MP vs official Alexandria-PBE": (0, (5.5, 1.7, 1.1, 1.7)),
    "alex-mp-20 vs official Alexandria-PBE": (0, (7.5, 2.8)),
    "MP vs alex-mp-20": "-",
}
METRIC_COLORS = {
    "f1": "#3B6FB6",
    "auprc": "#D95F59",
    "auroc": "#3A9D78",
    "balanced_accuracy": "#8A63A8",
    "stable_yield@1000": "#D49A2A",
}
METRIC_LABELS = {
    "f1": "F1",
    "auprc": "AUPRC",
    "auroc": "AUROC",
    "balanced_accuracy": "Balanced accuracy",
    "stable_yield@1000": "Stable yield@1k",
}


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 8.0,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9.0,
            "xtick.labelsize": 7.7,
            "ytick.labelsize": 7.7,
            "legend.fontsize": 7.3,
            "axes.linewidth": 0.65,
            "axes.edgecolor": "#53565A",
            "axes.spines.top": True,
            "axes.spines.right": True,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
        }
    )


def panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.04) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def clean_axis(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, color="#C9CDD2", linewidth=0.65, alpha=0.72)
    ax.set_axisbelow(True)


def export_figure(
    fig: plt.Figure,
    figure_dir: Path,
    stem: str,
    *,
    exact_canvas: bool = False,
) -> dict[str, object]:
    pdf = figure_dir / f"{stem}.pdf"
    tiff = figure_dir / f"{stem}.tiff"
    save_kwargs = {} if exact_canvas else {"bbox_inches": "tight", "pad_inches": 0.035}
    fig.savefig(pdf, **save_kwargs)
    fig.savefig(tiff, dpi=600, pil_kwargs={"compression": "tiff_lzw"}, **save_kwargs)
    width, height = fig.get_size_inches()
    plt.close(fig)
    return {
        "stem": stem,
        "width_cm": width / CM,
        "height_cm": height / CM,
        "pdf": str(pdf.resolve().relative_to(REPO)),
        "tiff": str(tiff.resolve().relative_to(REPO)),
        "tiff_dpi": 600,
        "vector_pdf": True,
        "final_width_contract_cm": 17.1 if width / CM > 10 else 8.3,
    }


def exact_plot_sample(curves: pd.DataFrame, per_curve: int = 650) -> pd.DataFrame:
    frames = []
    for _, group in curves.groupby(["model_name", "label_view"], sort=False):
        n = int(group["rank"].max())
        ranks = np.unique(
            np.concatenate(
                [
                    np.geomspace(1, n, per_curve).round().astype(int),
                    np.array([1, 10, 25, 50, 100, 300, 500, 1000, 5000, 10000, n]),
                ]
            )
        )
        ranks = ranks[(ranks >= 1) & (ranks <= n)]
        frames.append(group[group["rank"].isin(ranks)])
    return pd.concat(frames, ignore_index=True)


def figure1(curves: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    sample = exact_plot_sample(curves)
    curves.to_parquet(source_dir / "fig1_exact_discovery_curves_all_ranks.parquet", index=False)
    sample.to_csv(source_dir / "fig1_exact_discovery_curves.csv", index=False)
    fig, axes = plt.subplots(
        2, 3, figsize=(17.1 * CM, 10.2 * CM), sharey="row",
        gridspec_kw={"wspace": 0.13, "hspace": 0.13},
    )
    columns = ["mp_native", "consensus", "audit_view"]
    column_labels = ["MP-native", "Consensus", "Audit view"]
    rows = [
        ("stable_yield", "Stable yield"),
        ("recall", "Recall"),
    ]
    for row_idx, (metric, row_label) in enumerate(rows):
        for col_idx, (view, view_label) in enumerate(zip(columns, column_labels)):
            ax = axes[row_idx, col_idx]
            for model in REAL_MODELS:
                data = sample[
                    sample["model_name"].eq(model) & sample["label_view"].eq(view)
                ]
                ax.plot(
                    data["rank"], data[metric], color=MODEL_COLORS[model],
                    linestyle=MODEL_LINESTYLES[model], linewidth=2.05,
                    solid_capstyle="round", zorder=2,
                )
                endpoint = data.iloc[-1]
                ax.scatter(
                    endpoint["rank"], endpoint[metric], color=MODEL_COLORS[model],
                    marker="o", s=17, edgecolor="white", linewidth=0.45, zorder=3,
                )
            ax.axvline(1000, color="#69727D", linestyle=(0, (4, 3)), linewidth=0.7, zorder=0)
            ax.set_xlim(0, 36_801)
            ax.set_ylim(0, 1.0)
            ax.set_xticks([0, 10_000, 20_000, 30_000, 36_801])
            ax.xaxis.set_major_formatter(
                FuncFormatter(
                    lambda x, _: "36.8k" if x == 36_801 else (f"{int(x/1000)}k" if x else "0")
                )
            )
            if row_idx == 0:
                ax.set_title(view_label, pad=4, fontweight="normal")
                ax.tick_params(axis="x", labelbottom=False)
            if col_idx == 0:
                ax.set_ylabel(row_label)
            clean_axis(ax)
    panel_label(axes[0, 0], "a", x=0.04, y=0.86)
    panel_label(axes[1, 0], "b", x=0.04, y=0.86)
    model_handles = [
        Line2D(
            [0], [0], color=MODEL_COLORS[m], linestyle=MODEL_LINESTYLES[m],
            marker="o", markersize=3.7, linewidth=2.05, label=m,
        )
        for m in REAL_MODELS
    ]
    fig.supxlabel("Candidates evaluated, K", y=0.105, fontsize=8.5)
    fig.subplots_adjust(bottom=0.18, top=0.92, left=0.075, right=0.99)
    fig.legend(
        model_handles, [h.get_label() for h in model_handles],
        loc="lower center", bbox_to_anchor=(0.5, 0.015), ncol=4,
        columnspacing=1.5, handlelength=2.2,
    )
    return export_figure(fig, figure_dir, "fig1_sourceaware_discovery_curves")


def figure2(rolling: pd.DataFrame, density: pd.DataFrame, source_dir: Path, figure_dir: Path, metadata: dict[str, object]) -> dict[str, object]:
    rolling.to_csv(source_dir / "fig2_rolling_conflict_40mev.csv", index=False)
    density.to_csv(source_dir / "fig2_hull_distance_density.csv", index=False)
    (source_dir / "fig2_rolling_conflict_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    fig = plt.figure(figsize=(17.1 * CM, 10.0 * CM))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.56, 2.25], hspace=0.07)
    top = fig.add_subplot(gs[0])
    top.fill_between(density["bin_center_eV"], density["row_count"], step="mid", color="#6EC1D8", alpha=0.85, linewidth=0)
    top.plot(density["bin_center_eV"], density["row_count"], color="#008FC5", linewidth=1.75)
    top.set_xlim(0, 0.20)
    top.set_ylabel("Rows")
    top.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    top.tick_params(axis="x", labelbottom=False)
    top.grid(False)
    panel_label(top, "a", x=-0.075, y=0.90)

    ax = fig.add_subplot(gs[1], sharex=top)
    supported = rolling[rolling["supported"]]
    support_end = float(supported["reference_mp_native_e_above_hull_eV"].max())
    ax.axvspan(0.0, 0.04, color="#F6B6B2", alpha=0.30, linewidth=0)
    ax.axvspan(support_end + 0.0025, 0.20, color="#D9DDE1", alpha=0.38, linewidth=0)
    ax.axvline(0.04, color="#B96B68", linestyle=(0, (4, 3)), linewidth=0.75)
    ax.axvline(0.0, color="#333333", linewidth=0.8)
    for pair, data in rolling.groupby("source_pair", sort=False):
        data = data.sort_values("reference_mp_native_e_above_hull_eV")
        x = data["reference_mp_native_e_above_hull_eV"].to_numpy(float)
        y = data["endpoint_switch_rate"].to_numpy(float)
        lo = data["ci_low"].to_numpy(float)
        hi = data["ci_high"].to_numpy(float)
        color = PAIR_COLORS[pair]
        ax.fill_between(x, lo, hi, color=color, alpha=0.13, linewidth=0)
        ax.plot(
            x, y, color=color, linestyle=PAIR_STYLES[pair], linewidth=2.1,
            label=pair, solid_capstyle="round",
        )
    ax.text(0.005, 0.286, "Near-threshold\nlabel-risk zone", color="#8C3D3A", fontsize=7.4, va="top", fontweight="bold")
    window_x0, window_y0 = 0.154, 0.280
    ax.add_patch(Rectangle((window_x0, window_y0), 0.040, 0.006, fill=False, edgecolor="#35435E", linewidth=1.25, zorder=4))
    ax.text(window_x0 - 0.004, 0.286, "Rolling window = 40 meV", color="#20252B", fontsize=7.6, va="center", ha="right")
    ax.text(0.198, 0.266, "Wilson 95% CI", color="#4D5359", fontsize=6.6, va="top", ha="right")
    ax.text((support_end + 0.20) / 2, 0.145, "$n<1{,}000$\nmasked", color="#6B737C", fontsize=7.2, va="center", ha="center")
    ax.set_xlim(0, 0.20)
    ax.set_ylim(0, 0.30)
    ax.set_xticks([0, 0.04, 0.08, 0.12, 0.16, 0.20])
    ax.set_xlabel(r"MP-native $E_{\mathrm{above\ hull}}$ (eV atom$^{-1}$)")
    ax.set_ylabel("Rolling endpoint-switch rate")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend().remove()
    clean_axis(ax)
    panel_label(ax, "b", x=-0.075, y=1.02)
    fig.legend(
        handles, labels, loc="lower center", bbox_to_anchor=(0.54, 0.005),
        ncol=3, columnspacing=1.45, handlelength=2.7,
    )
    fig.subplots_adjust(bottom=0.17, top=0.98, left=0.09, right=0.99)
    return export_figure(fig, figure_dir, "fig2_near_threshold_discordance")


def figure3(denom: pd.DataFrame, conflicts: pd.DataFrame, decomp: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    denom.to_csv(source_dir / "fig3_denominator_hierarchy.csv", index=False)
    conflicts.to_csv(source_dir / "fig3_source_native_conflicts.csv", index=False)
    decomp.to_csv(source_dir / "fig3_conflict_decomposition.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(17.1 * CM, 8.1 * CM), gridspec_kw={"width_ratios": [0.95, 1.0, 1.28], "wspace": 0.66})

    ax = axes[0]
    order = ["F0", "D1", "D2", "D4", "D5"]
    d = denom.set_index("set_id").loc[order].reset_index()
    y = np.arange(len(d))[::-1]
    colors = ["#B9BDC2", "#4E79A7", "#76B7B2", "#A0CBE8", "#59A14F"]
    ax.barh(y, d["n_rows"], color=colors, height=0.62)
    ax.set_yticks(y, [f"{a}  {b}" for a, b in zip(d["set_id"], ["formula support", "MP–alex-mp-20", "three-source", "union target", "four-model"])])
    ax.set_xlim(0, 50_000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    for idx, (yi, value) in enumerate(zip(y, d["n_rows"])):
        ax.text(
            value - 650, yi, f"{value:,}", va="center", ha="right",
            fontsize=6.7, color="#222222" if idx == 0 else "white",
            fontweight="bold",
        )
    ax.set_xlabel("Rows")
    clean_axis(ax, "x")
    panel_label(ax, "a")

    ax = axes[1]
    c = conflicts.copy()
    c["label"] = c["source_pair"].replace({
        "MP vs official Alexandria-PBE": "MP–Alex-PBE (D2)",
        "alex-mp-20 vs official Alexandria-PBE": "alex-mp-20–Alex (D2)",
        "MP vs alex-mp-20": "MP–alex-mp-20 (D2)",
        "MP vs alex-mp-20 (strict full)": "MP–alex-mp-20 (D1)",
    })
    y = np.arange(len(c))[::-1]
    ax.barh(y, 100 * c["conflict_rate"], color=["#188DB8", "#E47D37", "#3A9D78", "#8297B8"], height=0.62)
    ax.set_yticks(y, c["label"])
    ax.set_xlim(0, 18)
    for yi, rate, count in zip(y, c["conflict_rate"], c["conflict_n"]):
        ax.text(100 * rate - 0.25, yi, f"{100*rate:.1f}%\n({count:,})", va="center", ha="right", fontsize=6.6, color="white", linespacing=0.9)
    ax.set_xlabel("Endpoint switches (%)")
    clean_axis(ax, "x")
    panel_label(ax, "b")

    ax = axes[2]
    dc = decomp.set_index("component")["n"]
    bar_names = ["Native conflicts", "Reconstructable\nnative", "Common-pool\nconflicts"]
    pieces = {
        "Phase-pool-sensitive": np.array([dc["phase_pool_sensitive"], dc["phase_pool_sensitive"], 0]),
        "Persistent": np.array([dc["persistent"], dc["persistent"], dc["persistent"]]),
        "Hidden common-pool": np.array([0, 0, dc["hidden_common_pool"]]),
        "Unreconstructable": np.array([dc["unreconstructable"], 0, 0]),
    }
    piece_colors = {"Phase-pool-sensitive": "#76B7B2", "Persistent": "#E15759", "Hidden common-pool": "#F2BE5C", "Unreconstructable": "#BAB0AC"}
    y = np.arange(3)[::-1]
    left = np.zeros(3)
    for name, values in pieces.items():
        ax.barh(y, values, left=left, color=piece_colors[name], height=0.60, label=name)
        for yi, lv, value in zip(y, left, values):
            if value >= 100:
                ax.text(lv + value / 2, yi, f"{int(value):,}", ha="center", va="center", fontsize=7.0, color="#222222")
        left += values
    ax.set_yticks(y, bar_names)
    ax.set_xlim(0, 6100)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    ax.set_xlabel("Rows")
    ax.annotate(
        "+5 unreconstructable", xy=(dc["phase_pool_sensitive"] + dc["persistent"], y[0]),
        xytext=(5550, y[0] + 0.43), ha="center", va="bottom", fontsize=6.7,
        color="#68615D", arrowprops={"arrowstyle": "-", "color": "#8B837D", "lw": 0.8},
    )
    legend_handles = [
        Patch(facecolor=piece_colors[name], edgecolor="none", label=name)
        for name in ["Phase-pool-sensitive", "Persistent", "Hidden common-pool"]
    ]
    ax.legend(
        handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.35),
        ncol=2, columnspacing=0.8, handlelength=1.4, labelspacing=0.35,
    )
    clean_axis(ax, "x")
    panel_label(ax, "c")
    fig.subplots_adjust(bottom=0.23, top=0.93, left=0.08, right=0.99)
    return export_figure(fig, figure_dir, "fig3_sourceaware_benchmark_layer")


def figure4(dominance: pd.DataFrame, slope: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    dominance.to_csv(source_dir / "fig4_uncertainty_dominance.csv", index=False)
    slope.to_csv(source_dir / "fig4_f1_rank_slopegraph.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(17.1 * CM, 8.2 * CM), gridspec_kw={"width_ratios": [1.08, 1.12, 1.0], "wspace": 0.50})

    ax = axes[0]
    metrics = list(PRIMARY_METRICS)
    ymap = {m: len(metrics) - 1 - i for i, m in enumerate(metrics)}
    jitter = {m: v for m, v in zip(REAL_MODELS, [-0.18, -0.06, 0.06, 0.18])}
    for model in REAL_MODELS:
        data = dominance[dominance["model_name"].eq(model)]
        ax.scatter(
            data["uncertainty_dominance_ratio"],
            [ymap[m] + jitter[model] for m in data["metric"]],
            color=MODEL_COLORS[model], marker=MODEL_MARKERS[model], s=24,
            edgecolor="white", linewidth=0.45, zorder=3, label=model,
        )
    ax.axvline(1, color="#8B2D2D", linestyle=(0, (4, 3)), linewidth=0.9)
    ax.set_xscale("log")
    ax.set_xlim(0.55, 15)
    ax.set_xticks([0.7, 1, 2, 5, 10], ["0.7", "1", "2", "5", "10"])
    ax.set_yticks(range(len(metrics)), [METRIC_LABELS[m] for m in metrics[::-1]])
    ax.set_xlabel("Label-view band / model margin")
    ax.text(1.08, len(metrics) - 0.55, "equal influence", ha="left", va="top", color="#8B2D2D", fontsize=6.8)
    clean_axis(ax, "x")
    panel_label(ax, "a")

    ax = axes[1]
    views = ["mp_native", "alex_pbe_native", "common_pool", "consensus", "audit_view"]
    view_labels = ["MP", "Alex-PBE", "Common", "Consensus", "Audit"]
    x = np.arange(len(views))
    for model in REAL_MODELS:
        data = slope[slope["model_name"].eq(model)].set_index("label_view").reindex(views)
        ax.plot(x, data["rank"], color=MODEL_COLORS[model], marker=MODEL_MARKERS[model], markersize=3.3, linewidth=1.5, label=model)
    ax.set_xlim(-0.18, len(views) - 0.35)
    ax.set_ylim(4.35, 0.65)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_xticks(x, view_labels, rotation=25, ha="right")
    ax.set_ylabel("F1 rank among real models")
    clean_axis(ax)
    panel_label(ax, "b")

    ax = axes[2]
    for metric, data in dominance.groupby("metric"):
        for _, row in data.iterrows():
            ax.scatter(
                row["between_model_margin_median"], row["label_view_band"],
                color=METRIC_COLORS[metric], marker=MODEL_MARKERS[row["model_name"]],
                s=24, alpha=0.88, edgecolor="white", linewidth=0.35,
            )
    low = min(dominance["between_model_margin_median"].min(), dominance["label_view_band"].min()) * 0.75
    high = max(dominance["between_model_margin_median"].max(), dominance["label_view_band"].max()) * 1.25
    ax.plot([low, high], [low, high], color="#8B2D2D", linestyle=(0, (4, 3)), linewidth=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(low, high)
    ax.set_ylim(low, high)
    ax.set_xlabel("Model margin")
    ax.set_ylabel("Label-view band")
    offsets = {
        "f1": (-14, 14), "auprc": (8, -10), "auroc": (8, 9),
        "balanced_accuracy": (8, -10), "stable_yield@1000": (-2, 15),
    }
    for metric, data in dominance.groupby("metric"):
        x0 = float(data["between_model_margin_median"].median())
        y0 = float(data["label_view_band"].median())
        ax.annotate(METRIC_LABELS[metric], (x0, y0), xytext=offsets[metric], textcoords="offset points", fontsize=6.5, color=METRIC_COLORS[metric], fontweight="bold")
    clean_axis(ax, "both")
    panel_label(ax, "c")
    model_handles = [Line2D([0], [0], marker=MODEL_MARKERS[m], color=MODEL_COLORS[m], linewidth=1.5, markersize=4, label=m) for m in REAL_MODELS]
    fig.legend(model_handles, [h.get_label() for h in model_handles], loc="lower center", bbox_to_anchor=(0.5, 0.01), ncol=4, columnspacing=1.3, handlelength=1.6)
    fig.subplots_adjust(bottom=0.22, top=0.93, left=0.08, right=0.99)
    return export_figure(fig, figure_dir, "fig4_model_rank_audit")


def figure5(exact: pd.DataFrame, unsupported: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    exact.to_csv(source_dir / "fig5_exact_matched_screened_candidates.csv", index=False)
    unsupported.to_csv(source_dir / "fig5_formula_only_unmatched_generated_pools.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(17.1 * CM, 8.2 * CM), gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.35})
    screen = exact[exact["pipeline_type"].eq("screening_pipeline_not_true_generator")].copy()
    order = [
        "alignn_ff_screened_sourceaware_top5000",
        "chgnet_screened_sourceaware_top5000",
        "m3gnet_screened_sourceaware_top5000",
        "mace_mp_screened_sourceaware_top5000",
        "CHGNet_screened_public_hull_top5000",
    ]
    screen = screen.set_index("pipeline_name").reindex(order).dropna(subset=["candidate_n"]).reset_index()
    names = ["ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP", "CHGNet public"]
    ax = axes[0]
    y = np.arange(len(screen))[::-1]
    for i, (column, label, color, marker) in enumerate(
        [
            ("mp_native_stable_yield", "MP-native", "#4E79A7", "o"),
            ("consensus_stable_yield", "Consensus", "#3A9D78", "s"),
            ("audit_view_stable_yield", "Audit view", "#E47D37", "D"),
        ]
    ):
        ax.scatter(screen[column], y + (0.16 - i * 0.16), color=color, marker=marker, s=27, label=label, zorder=3, edgecolor="white", linewidth=0.4)
    for yi, lo, hi in zip(y, screen["audit_view_stable_yield"], screen["mp_native_stable_yield"]):
        ax.plot([lo, hi], [yi - 0.16, yi + 0.16], color="#B7BDC4", linewidth=1.2, zorder=1)
    ax.scatter(screen["source_uncertain_fraction"], y - 0.30, color="#8B2D2D", marker="x", s=23, linewidth=1.2, label="Source-uncertain", zorder=3)
    ax.set_yticks(y, names)
    ax.set_xlim(0.20, 0.44)
    ax.set_xlabel("Fraction of exact-matched candidates")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.56), ncol=2, columnspacing=1.0, handletextpad=0.4)
    clean_axis(ax, "x")
    panel_label(ax, "a")

    generated = unsupported[unsupported["pipeline_type"].isin(["true_generator", "available_crystal_generation_pipeline"])].copy()
    preferred = ["MatterGen_hf_base_smoke_unconditional", "MatterGen_pilot_5k_public_safe_formulas", "PGCGM_public_safe_generated_pool"]
    generated = generated.set_index("pipeline_name").reindex(preferred).dropna(subset=["candidate_n"]).reset_index()
    names = ["MatterGen smoke", "MatterGen formula pool", "PGCGM pool"]
    ax = axes[1]
    y = np.arange(len(generated))[::-1]
    bottom = np.zeros(len(generated))
    for column, label, color in [
        ("formula_only_overlap_fraction", "Formula-only", "#F2BE5C"),
        ("unsupported_no_formula_overlap_fraction", "Unmatched", "#B9BDC2"),
    ]:
        values = generated[column].to_numpy(float)
        ax.barh(y, values, left=bottom, color=color, height=0.58, label=label)
        bottom += values
    ax.set_yticks(y, names)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Candidate-pool fraction")
    for yi, formula, unmatched in zip(y, generated["formula_only_overlap_fraction"], generated["unsupported_no_formula_overlap_fraction"]):
        ax.text(0.98, yi, "0 exact matches", ha="right", va="center", fontsize=6.7, color="#4D5359", fontweight="bold")
        if formula >= 0.025:
            ax.text(
                formula + 0.012, yi, f"{100*formula:.1f}% formula-only",
                ha="left", va="center", fontsize=6.4, color="#765213",
                fontweight="bold",
            )
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.56), ncol=2, columnspacing=0.9, handlelength=1.6)
    clean_axis(ax, "x")
    panel_label(ax, "b")
    fig.subplots_adjust(bottom=0.37, top=0.93, left=0.12, right=0.99)
    return export_figure(fig, figure_dir, "fig5_candidate_consequence")


def toc_graphic(curves: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    data = exact_plot_sample(curves, per_curve=120)
    data = data[(data["model_name"].eq("MACE-MP")) & (data["label_view"].isin(DISCOVERY_LABEL_VIEWS))]
    data.to_csv(source_dir / "toc_graphic_source.csv", index=False)
    fig, ax = plt.subplots(figsize=(8.0 * CM, 4.0 * CM))
    for view in DISCOVERY_LABEL_VIEWS:
        d = data[data["label_view"].eq(view)]
        ax.plot(d["rank"], d["stable_yield"], linestyle=VIEW_STYLES[view], color=MODEL_COLORS["MACE-MP"], linewidth=1.65, label=VIEW_LABELS[view])
    ax.axvline(1000, color="#6E7781", linestyle=(0, (4, 3)), linewidth=0.65)
    ax.set_xlim(0, 12_000)
    ax.set_ylim(0.15, 0.70)
    ax.set_xlabel("Candidates evaluated")
    ax.set_ylabel("Stable yield")
    ax.legend(loc="upper right", fontsize=5.5, handlelength=2.4)
    clean_axis(ax)
    fig.text(0.02, 0.97, "Source-aware labels turn one ranking into multiple discovery outcomes", ha="left", va="top", fontsize=6.5, fontweight="bold")
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.22, top=0.82)
    # RSC specifies a maximum 8 cm x 4 cm TOC canvas.  Do not use a tight
    # bounding box here because it can expand the saved physical page size.
    return export_figure(fig, figure_dir, "toc_graphic", exact_canvas=True)


def copy_manuscript_figures(figure_dir: Path, manuscript_figure_dir: Path | None) -> None:
    if manuscript_figure_dir is None:
        return
    ensure_dir(manuscript_figure_dir)
    for path in figure_dir.glob("fig[1-5]_*.pdf"):
        shutil.copy2(path, manuscript_figure_dir / path.name)
    for path in figure_dir.glob("fig[1-5]_*.tiff"):
        shutil.copy2(path, manuscript_figure_dir / path.name)
    for path in figure_dir.glob("toc_graphic.*"):
        shutil.copy2(path, manuscript_figure_dir / path.name)


def build(args: argparse.Namespace) -> list[dict[str, object]]:
    set_style()
    out = ensure_dir(args.out)
    source_dir = ensure_dir(out / "figure_source_data")
    figure_dir = ensure_dir(out / "figures")
    write_claims_outputs(out, args.phase1, args.phase2)

    curves = exact_discovery_curves(args.phase1, args.phase2)
    metrics, topk = exact_primary_metrics(args.phase1, args.phase2)
    metrics.to_csv(out / "primary_exact_real_model_metrics.csv", index=False)
    topk.to_csv(out / "primary_exact_real_model_topk.csv", index=False)
    dominance, ranks, slope = uncertainty_dominance_tables(metrics, topk)
    dominance.to_csv(out / "primary_real_model_uncertainty_dominance.csv", index=False)
    ranks.to_csv(out / "primary_real_model_rankings.csv", index=False)
    rolling, density, rolling_meta = rolling_conflict_table(args.phase1)
    denom = denominator_summary(args.phase1, args.phase2)
    conflicts = pairwise_native_conflicts(args.phase1)
    decomp = conflict_decomposition(args.phase1)
    exact_candidates, unsupported_candidates = candidate_claim_tables(args.phase2)
    rank_flip_normalisation(args.phase2).to_csv(out / "rank_flip_normalisation.csv", index=False)

    records = [
        figure1(curves, source_dir, figure_dir),
        figure2(rolling, density, source_dir, figure_dir, rolling_meta),
        figure3(denom, conflicts, decomp, source_dir, figure_dir),
        figure4(dominance, slope, source_dir, figure_dir),
        figure5(exact_candidates, unsupported_candidates, source_dir, figure_dir),
        toc_graphic(curves, source_dir, figure_dir),
    ]
    copy_manuscript_figures(figure_dir, args.manuscript_figures)
    (out / "figure_qa.json").write_text(json.dumps({"status": "PASS", "figures": records}, indent=2) + "\n")
    (out / "toc_text.txt").write_text("Source-aware label views turn a fixed crystal ranking into distinct discovery curves, exposing benchmark uncertainty in stable yield and recall without treating any diagnostic label as physical truth.\n")
    return records


def check_outputs(out: Path) -> None:
    expected = [
        out / "manuscript_claims.json",
        out / "manuscript_claims_audit.md",
        out / "primary_exact_real_model_metrics.csv",
        out / "primary_exact_real_model_topk.csv",
        out / "figure_source_data" / "fig1_exact_discovery_curves.csv",
        out / "figure_source_data" / "fig1_exact_discovery_curves_all_ranks.parquet",
        out / "figure_source_data" / "fig2_rolling_conflict_40mev.csv",
        out / "figure_source_data" / "fig3_conflict_decomposition.csv",
        out / "figure_source_data" / "fig4_uncertainty_dominance.csv",
        out / "figure_source_data" / "fig5_exact_matched_screened_candidates.csv",
        out / "figures" / "fig1_sourceaware_discovery_curves.pdf",
        out / "figures" / "fig2_near_threshold_discordance.pdf",
        out / "figures" / "fig3_sourceaware_benchmark_layer.pdf",
        out / "figures" / "fig4_model_rank_audit.pdf",
        out / "figures" / "fig5_candidate_consequence.pdf",
        out / "figures" / "toc_graphic.pdf",
    ]
    missing = [str(path) for path in expected if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise SystemExit("Missing or empty submission figure outputs:\n" + "\n".join(missing))
    claims = json.loads((out / "manuscript_claims.json").read_text())
    if not all(claims["conflict_identities"].values()):
        raise SystemExit("Conflict identities do not close")
    if claims["model_evidence"]["primary_real_model_n"] != 4:
        raise SystemExit("Primary model evidence is not restricted to four real models")
    if len((out / "toc_text.txt").read_text().strip()) > 250:
        raise SystemExit("TOC text exceeds 250 characters")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1", type=Path, default=DEFAULT_PHASE1)
    parser.add_argument("--phase2", type=Path, default=DEFAULT_PHASE2)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manuscript-figures", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build(args)
    if args.check:
        check_outputs(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
