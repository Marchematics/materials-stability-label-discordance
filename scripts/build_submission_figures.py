#!/usr/bin/env python3
"""Build Digital Discovery submission figures from released benchmark rows.

All curves are row-level cumulative calculations. No spline interpolation is
used.

Figure 1/2 use the presentation grammar of the MIT-licensed Matbench Discovery
v1.1.0 plotting scripts retained under ``third_party/``: Light24 colours,
line-dash identities, a marginal density panel, external legends and an explicit
rolling-window scale bar. This is a style reference only; numerical results are
calculated from released SourceAware outputs below.
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
    # Plotly Light24 entries used in the Matbench Discovery reference figure.
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
PAIR_SHORT_LABELS = {
    "MP vs official Alexandria-PBE": "MP vs Alex-PBE",
    "alex-mp-20 vs official Alexandria-PBE": "alex-mp-20 vs Alex-PBE",
    "MP vs alex-mp-20": "MP vs alex-mp-20",
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


def panel_label(ax: plt.Axes, label: str, x: float = -0.21, y: float = 1.04) -> None:
    """Add a restrained, consistently placed panel label."""
    ax.text(
        x, y, label, transform=ax.transAxes, fontsize=8.7, fontweight="bold",
        va="bottom", ha="left", clip_on=False,
    )


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
    """Plot exact discovery curves using the cumulative-campaign grammar.

    The two panels mirror the discovery decision a reader makes: how many
    selected candidates are stable, and how much of the corresponding stable
    set is recovered. Colour identifies a model and line style identifies a
    label view.  The renderer draws the complete rank-by-rank calculation, not
    an interpolation of the fixed top-K summaries.
    """
    sample = exact_plot_sample(curves)
    curves.to_parquet(source_dir / "fig1_exact_discovery_curves_all_ranks.parquet", index=False)
    sample.to_csv(source_dir / "fig1_exact_discovery_curves.csv", index=False)

    # The practical campaign range is intentionally shown at full resolution.
    # Restricting the canvas to 10k retains the relevant screening budgets while
    # avoiding a compressed, visually uninformative tail.
    campaign_max = 10_000
    plot_data = curves[
        curves["label_view"].isin(DISCOVERY_LABEL_VIEWS)
        & curves["rank"].le(campaign_max)
    ].copy()
    fig = plt.figure(figsize=(17.1 * CM, 8.6 * CM))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.43], wspace=0.30)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    legend_ax = fig.add_subplot(grid[0, 2])
    legend_ax.axis("off")

    # Reference style: colour represents model identity; dash represents the
    # label view.  This keeps the comparison readable even where curves cross.
    view_styles = {
        "audit_view": "-",
        "mp_native": (0, (6.0, 2.4)),
        "consensus": (0, (1.15, 1.55)),
    }
    # Draw the less visually dominant views first, then foreground the audit
    # view. This preserves the source-aware comparison in dense early ranks.
    view_order = ["consensus", "mp_native", "audit_view"]
    panels = [
        ("stable_yield", "Stable yield", "Stable candidates / candidates evaluated"),
        ("recall", "Recall", "Stable set recovered"),
    ]
    for panel_idx, (ax, (metric, title, ylabel)) in enumerate(zip(axes, panels)):
        for view in view_order:
            for model in REAL_MODELS:
                data = plot_data[
                    plot_data["model_name"].eq(model) & plot_data["label_view"].eq(view)
                ]
                if data.empty:
                    continue
                ax.plot(
                    data["rank"], data[metric],
                    color=MODEL_COLORS[model], linestyle=view_styles[view],
                    linewidth=1.95 if view == "audit_view" else 1.40,
                    alpha=1.0 if view == "audit_view" else 0.80,
                    solid_capstyle="round", zorder=2,
                )
                # One endpoint marker per model prevents a 12-marker cluster.
                if view == "audit_view":
                    endpoint = data.iloc[-1]
                    ax.scatter(
                        endpoint["rank"], endpoint[metric], color=MODEL_COLORS[model],
                        marker=MODEL_MARKERS[model], s=19, edgecolor="white",
                        linewidth=0.45, zorder=3,
                    )
        ax.axvline(1000, color="#8090A3", linestyle=(0, (5, 4)), linewidth=0.75, zorder=0)
        if panel_idx == 0:
            ax.text(0.13, 0.95, "$K=1{,}000$", color="#596878", fontsize=7.1,
                    va="top", transform=ax.transAxes)
        ax.set_xlim(0, campaign_max)
        ax.set_xticks([0, 2000, 4000, 6000, 8000, 10_000])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: "10k" if x == 10_000 else (f"{int(x/1000)}k" if x else "0")))
        # Stable yield is a probability. Keep the full [0, 1] scale so that
        # the very-small-budget behaviour is not clipped or visually implied.
        ax.set_ylim((0.0, 1.0) if metric == "stable_yield" else (0.0, 0.40))
        ax.set_xlabel("Candidates evaluated, $K$")
        ax.set_ylabel(ylabel)
        ax.set_title(title, pad=5, fontweight="normal")
        clean_axis(ax)
        panel_label(ax, chr(ord("a") + panel_idx))

    model_handles = [
        Line2D(
            [0], [0], color=MODEL_COLORS[m], marker=MODEL_MARKERS[m],
            markersize=4.1, linewidth=2.0, label=m,
        )
        for m in REAL_MODELS
    ]
    view_handles = [
        Line2D([0], [0], color="#39424E", linestyle=view_styles[v], linewidth=1.9, label=VIEW_LABELS[v])
        for v in ["audit_view", "mp_native", "consensus"]
    ]
    legend_ax.text(0.02, 0.93, "Models", transform=legend_ax.transAxes, fontsize=7.4, fontweight="bold", va="top")
    leg_models = legend_ax.legend(
        model_handles, [h.get_label() for h in model_handles], loc="upper left",
        bbox_to_anchor=(0.0, 0.88), frameon=False, handlelength=2.1,
        handletextpad=0.55, labelspacing=0.70, borderaxespad=0,
    )
    legend_ax.add_artist(leg_models)
    legend_ax.text(0.02, 0.42, "Label view", transform=legend_ax.transAxes, fontsize=7.4, fontweight="bold", va="top")
    legend_ax.legend(
        view_handles, [h.get_label() for h in view_handles], loc="upper left",
        bbox_to_anchor=(0.0, 0.37), frameon=False, handlelength=2.7,
        handletextpad=0.55, labelspacing=0.70, borderaxespad=0,
    )
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.16, top=0.89)
    return export_figure(fig, figure_dir, "fig1_sourceaware_discovery_curves")


def figure2(rolling: pd.DataFrame, density: pd.DataFrame, source_dir: Path, figure_dir: Path, metadata: dict[str, object]) -> dict[str, object]:
    rolling.to_csv(source_dir / "fig2_rolling_conflict_40mev.csv", index=False)
    density.to_csv(source_dir / "fig2_hull_distance_density.csv", index=False)
    (source_dir / "fig2_rolling_conflict_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    # Use the compact density-plus-rolling-window grammar at a single-column
    # width. The short source-pair names and two-row legend preserve legibility
    # at 8.3 cm without moving explanatory text into the plotted data region.
    fig = plt.figure(figsize=(8.3 * CM, 10.4 * CM))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.53, 2.23], hspace=0.07)
    top = fig.add_subplot(gs[0])
    top.fill_between(density["bin_center_eV"], density["row_count"], step="mid", color="#6EC1D8", alpha=0.85, linewidth=0)
    top.plot(density["bin_center_eV"], density["row_count"], color="#008FC5", linewidth=1.75)
    top.set_xlim(0, 0.20)
    top.set_ylabel("Rows")
    top.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    top.tick_params(axis="y", labelsize=6.35)
    top.tick_params(axis="x", labelbottom=False)
    top.grid(False)
    panel_label(top, "a", x=-0.16, y=0.88)

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
            label=PAIR_SHORT_LABELS[pair], solid_capstyle="round",
        )
    ax.text(0.0045, 0.286, "Near-threshold\nrisk zone", color="#8C3D3A", fontsize=6.45, va="top", fontweight="bold", linespacing=0.90)
    window_x0, window_y0 = 0.159, 0.280
    ax.add_patch(Rectangle((window_x0, window_y0), 0.034, 0.0055, fill=False, edgecolor="#35435E", linewidth=1.0, zorder=4))
    ax.text(window_x0 - 0.004, 0.286, "40-meV window", color="#20252B", fontsize=6.25, va="center", ha="right")
    ax.text(0.198, 0.266, "Chemical-system\nbootstrap 95% CI", color="#4D5359", fontsize=5.45, va="top", ha="right", linespacing=0.92)
    ax.text((support_end + 0.20) / 2, 0.145, "$n<1{,}000$ or <20 systems\nmasked", color="#6B737C", fontsize=5.9, va="center", ha="center")
    ax.set_xlim(0, 0.20)
    ax.set_ylim(0, 0.30)
    ax.set_xticks([0, 0.04, 0.08, 0.12, 0.16, 0.20])
    ax.tick_params(axis="both", labelsize=6.45)
    ax.set_xlabel(r"MP-native $E_{\mathrm{above\ hull}}$ (eV atom$^{-1}$)")
    ax.set_ylabel("Rolling endpoint-switch rate")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend().remove()
    clean_axis(ax)
    panel_label(ax, "b", x=-0.16, y=1.02)
    fig.legend(
        handles, labels, loc="lower center", bbox_to_anchor=(0.50, 0.006),
        ncol=2, columnspacing=0.90, handlelength=2.25, fontsize=5.9,
        labelspacing=0.55,
    )
    fig.subplots_adjust(bottom=0.19, top=0.98, left=0.17, right=0.98)
    return export_figure(fig, figure_dir, "fig2_near_threshold_discordance")


def figure3(denom: pd.DataFrame, conflicts: pd.DataFrame, decomp: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    denom.to_csv(source_dir / "fig3_denominator_hierarchy.csv", index=False)
    conflicts.to_csv(source_dir / "fig3_source_native_conflicts.csv", index=False)
    decomp.to_csv(source_dir / "fig3_conflict_decomposition.csv", index=False)
    fig = plt.figure(figsize=(17.1 * CM, 8.8 * CM))
    # The decomposition is the interpretive panel, so it receives more width
    # than the denominator and pairwise-switch summaries.
    grid = fig.add_gridspec(1, 3, width_ratios=[0.82, 1.08, 1.52], wspace=0.46)
    axes = [fig.add_subplot(grid[0, idx]) for idx in range(3)]

    # a | Denominator hierarchy. F0 is explicitly named as support rather
    # than plotted as an apparent predecessor of the exact denominators.
    ax = axes[0]
    order = ["F0", "D1", "D2", "D4", "D5"]
    d = denom.set_index("set_id").loc[order].reset_index()
    y = np.arange(len(d))[::-1]
    colors = ["#B9BDC2", "#4E79A7", "#76B7B2", "#A0CBE8", "#59A14F"]
    labels = ["F0  formula support", "D1  exact pair", "D2  three-source", "D4  union status", "D5  four-model"]
    ax.barh(y, d["n_rows"], color=colors, height=0.62)
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 50_000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    for idx, (yi, value) in enumerate(zip(y, d["n_rows"])):
        ax.text(
            value - 650, yi, f"{value:,}", va="center", ha="right",
            fontsize=6.8, color="#222222" if idx == 0 else "white",
            fontweight="bold",
        )
    ax.set_xlabel("Rows")
    ax.set_title("Benchmark cohorts", pad=8, fontweight="normal")
    clean_axis(ax, "x")
    panel_label(ax, "a")

    # b | Vertical lollipops avoid long source-pair labels colliding with the
    # neighbouring denominator panel, while preserving counts and rates.
    ax = axes[1]
    c = conflicts.copy()
    category = {
        "MP vs official Alexandria-PBE": (0.0, "o"),
        "alex-mp-20 vs official Alexandria-PBE": (1.20, "o"),
        "MP vs alex-mp-20": (2.42, "o"),
        "MP vs alex-mp-20 (strict full)": (2.70, "s"),
    }
    x = np.array([category[pair][0] for pair in c["source_pair"]])
    markers = [category[pair][1] for pair in c["source_pair"]]
    rates = 100 * c["conflict_rate"].to_numpy(float)
    colors = ["#188DB8", "#E47D37", "#3A9D78", "#8297B8"]
    ax.vlines(x, 0, rates, color=colors, linewidth=2.0, zorder=2)
    for xi, marker, rate, color in zip(x, markers, rates, colors):
        ax.scatter(xi, rate, color=color, marker=marker, s=34, zorder=3, edgecolor="white", linewidth=0.5)
    # Exact rates and counts are reported in the caption/source table.  The
    # compact panel retains only the lollipop positions, eliminating callout
    # collisions between the two MP--alex-mp-20 comparisons.
    ax.set_xlim(-0.55, 3.15)
    ax.set_ylim(0, 18.3)
    ax.set_xticks(
        [0, 1.20, 2.56],
        ["MP–\nAlex-PBE", "alex-mp-20–\nAlex-PBE", "MP–alex-mp-20"],
        fontsize=6.05,
        linespacing=0.90,
    )
    ax.set_ylabel("Endpoint switches (%)")
    ax.set_title("Source-native switches", pad=8, fontweight="normal")
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="#4D5359", linewidth=0, markersize=4, label="D2"),
            Line2D([0], [0], marker="s", color="#4D5359", linewidth=0, markersize=4, label="D1"),
        ],
        loc="upper right", fontsize=5.8, ncol=2, columnspacing=0.65,
        handletextpad=0.3, borderaxespad=0.2,
    )
    clean_axis(ax, "y")
    panel_label(ax, "b")

    # c | The stacked bars present the three count identities in one aligned
    # coordinate system. The five unreconstructable native rows are retained
    # as a slate sliver at the end of the top bar and stated in the caption.
    ax = axes[2]
    dc = decomp.set_index("component")["n"]
    bar_names = ["Native\nconflicts", "Reconstructable\nnative", "Common-pool\nconflicts"]
    pieces = {
        "Phase-pool-sensitive": np.array([dc["phase_pool_sensitive"], dc["phase_pool_sensitive"], 0]),
        "Persistent": np.array([dc["persistent"], dc["persistent"], dc["persistent"]]),
        "Hidden common-pool": np.array([0, 0, dc["hidden_common_pool"]]),
        "Unreconstructable": np.array([dc["unreconstructable"], 0, 0]),
    }
    piece_colors = {
        "Phase-pool-sensitive": "#76B7B2",
        "Persistent": "#E15759",
        "Hidden common-pool": "#F2BE5C",
        "Unreconstructable": "#7F8790",
    }
    text_colors = {
        "Phase-pool-sensitive": "#1F3437",
        "Persistent": "white",
        "Hidden common-pool": "#4C3B16",
        "Unreconstructable": "white",
    }
    y = np.arange(3)[::-1]
    left = np.zeros(3)
    for name, values in pieces.items():
        ax.barh(y, values, left=left, color=piece_colors[name], height=0.60, label=name)
        for yi, lv, value in zip(y, left, values):
            if value >= 100:
                ax.text(lv + value / 2, yi, f"{int(value):,}", ha="center", va="center", fontsize=6.8, color=text_colors[name])
        left += values
    # Short conventional y-axis labels prevent the category text from
    # intruding into either the bar values or the neighbouring panel.
    ax.set_yticks(y, ["Native", "Reconst.", "Common"], fontsize=6.5)
    ax.tick_params(axis="y", pad=2.8)
    ax.set_xlim(0, 6000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k" if x else "0"))
    ax.set_xlabel("Rows")
    ax.set_title("Matched common-pool decomposition", pad=8, fontweight="normal")
    legend_handles = [
        Patch(facecolor=piece_colors[name], edgecolor="none", label=name)
        for name in ["Phase-pool-sensitive", "Persistent", "Hidden common-pool", "Unreconstructable"]
    ]
    ax.legend(
        handles=legend_handles, loc="lower center", bbox_to_anchor=(0.48, -0.39),
        ncol=2, columnspacing=0.85, handlelength=1.35, labelspacing=0.42,
    )
    clean_axis(ax, "x")
    panel_label(ax, "c")
    fig.subplots_adjust(bottom=0.29, top=0.89, left=0.075, right=0.99)
    return export_figure(fig, figure_dir, "fig3_sourceaware_benchmark_layer")


def figure4(dominance: pd.DataFrame, slope: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    dominance.to_csv(source_dir / "fig4_uncertainty_dominance.csv", index=False)
    slope.to_csv(source_dir / "fig4_f1_rank_slopegraph.csv", index=False)
    # Give the uncertainty-dominance comparison a full-width hero panel.  The
    # two lower panels then explain how the same evidence affects ranks and
    # the absolute size of the metric bands.
    fig = plt.figure(figsize=(17.1 * CM, 11.8 * CM))
    grid = fig.add_gridspec(
        2, 2, height_ratios=[1.06, 1.0], width_ratios=[1.0, 1.0],
        hspace=0.61, wspace=0.48,
    )
    ax_a = fig.add_subplot(grid[0, :])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[1, 1])

    # a | Values above the explicit horizontal reference line indicate that
    # label-view variation exceeds the median model-to-model margin.
    ax = ax_a
    metrics = list(PRIMARY_METRICS)
    xmap = {metric: idx for idx, metric in enumerate(metrics)}
    jitter = {model: value for model, value in zip(REAL_MODELS, [-0.20, -0.067, 0.067, 0.20])}
    for model in REAL_MODELS:
        data = dominance[dominance["model_name"].eq(model)]
        ax.scatter(
            [xmap[metric] + jitter[model] for metric in data["metric"]],
            data["uncertainty_dominance_ratio"],
            color=MODEL_COLORS[model], marker=MODEL_MARKERS[model], s=31,
            edgecolor="white", linewidth=0.45, zorder=3, label=model,
        )
    ax.axhline(1, color="#8B2D2D", linestyle=(0, (4, 3)), linewidth=0.9, zorder=1)
    ax.text(
        0.995, 1.12, "equal label and model variation", transform=ax.get_yaxis_transform(),
        color="#8B2D2D", fontsize=6.5, ha="right", va="bottom",
    )
    ax.set_yscale("log")
    ax.set_ylim(0.55, 16.5)
    ax.set_yticks([0.7, 1, 2, 5, 10], ["0.7", "1", "2", "5", "10"])
    ax.set_xlim(-0.55, len(metrics) - 0.45)
    ax.set_xticks(range(len(metrics)), [METRIC_LABELS[m] for m in metrics])
    ax.set_ylabel("Label-view band / model margin", fontsize=7.8, labelpad=3.5)
    ax.set_title("Label uncertainty relative to model margins", pad=8, fontweight="normal")
    clean_axis(ax, "y")
    panel_label(ax, "a", x=-0.055, y=1.04)
    model_handles = [
        Line2D([0], [0], marker=MODEL_MARKERS[m], color=MODEL_COLORS[m],
               linewidth=1.5, markersize=4.1, label=m)
        for m in REAL_MODELS
    ]
    ax.legend(
        model_handles, [h.get_label() for h in model_handles],
        loc="upper right", ncol=4, bbox_to_anchor=(0.99, 1.01),
        columnspacing=1.2, handlelength=1.6, handletextpad=0.45,
    )

    # b | Rank paths retain the fixed identities used in panel a.
    ax = ax_b
    views = ["mp_native", "alex_pbe_native", "common_pool", "consensus", "audit_view"]
    view_labels = ["MP", "Alex-PBE", "Common", "Consensus", "Audit"]
    x = np.arange(len(views))
    for model in REAL_MODELS:
        data = slope[slope["model_name"].eq(model)].set_index("label_view").reindex(views)
        ax.plot(x, data["rank"], color=MODEL_COLORS[model], marker=MODEL_MARKERS[model], markersize=3.7, linewidth=1.65, label=model)
    ax.set_xlim(-0.20, len(views) - 0.30)
    ax.set_ylim(4.35, 0.65)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_xticks(x, view_labels, rotation=22, ha="right")
    ax.set_ylabel("F1 rank among real models")
    ax.set_title("F1 rank across label views", pad=8, fontweight="normal")
    clean_axis(ax)
    panel_label(ax, "b", x=-0.11, y=1.04)

    # c | Model colour and marker remain consistent across all panels. Metric
    # labels are positioned with short leader lines so that the three large
    # upper-left bands remain readable at journal width.
    ax = ax_c
    for _, row in dominance.iterrows():
        ax.scatter(
            row["between_model_margin_median"], row["label_view_band"],
            color=MODEL_COLORS[row["model_name"]], marker=MODEL_MARKERS[row["model_name"]],
            s=31, alpha=0.92, edgecolor="white", linewidth=0.4, zorder=3,
        )
    low = min(dominance["between_model_margin_median"].min(), dominance["label_view_band"].min()) * 0.75
    high = max(dominance["between_model_margin_median"].max(), dominance["label_view_band"].max()) * 1.25
    ax.plot([low, high], [low, high], color="#8B2D2D", linestyle=(0, (4, 3)), linewidth=0.85, zorder=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(low, high)
    ax.set_ylim(low, high)
    ax.set_xlabel("Median model margin")
    ax.set_ylabel("Label-view band")
    ax.set_title("Band versus model margin", pad=8, fontweight="normal")
    label_positions = {
        "f1": (0.043, 0.325),
        "auprc": (0.0175, 0.202),
        "auroc": (0.031, 0.032),
        "balanced_accuracy": (0.048, 0.0145),
        "stable_yield@1000": (0.094, 0.215),
    }
    for metric, data in dominance.groupby("metric"):
        x0 = float(data["between_model_margin_median"].median())
        y0 = float(data["label_view_band"].median())
        ax.annotate(
            METRIC_LABELS[metric], xy=(x0, y0), xytext=label_positions[metric],
            textcoords="data", fontsize=6.55, color=METRIC_COLORS[metric],
            fontweight="bold", ha="center", va="center",
            arrowprops={"arrowstyle": "-", "color": METRIC_COLORS[metric], "lw": 0.65, "alpha": 0.75},
        )
    clean_axis(ax, "both")
    panel_label(ax, "c", x=-0.11, y=1.04)
    fig.subplots_adjust(bottom=0.11, top=0.94, left=0.090, right=0.99)
    return export_figure(fig, figure_dir, "fig4_model_rank_audit")


def figure5(exact: pd.DataFrame, unsupported: pd.DataFrame, source_dir: Path, figure_dir: Path) -> dict[str, object]:
    exact.to_csv(source_dir / "fig5_exact_matched_screened_candidates.csv", index=False)
    unsupported.to_csv(source_dir / "fig5_formula_only_unmatched_generated_pools.csv", index=False)
    fig = plt.figure(figsize=(17.1 * CM, 8.5 * CM))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.38, 0.94], wspace=0.54)
    axes = [fig.add_subplot(grid[0, idx]) for idx in range(2)]
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
    point_specs = [
        ("mp_native_stable_yield", "MP-native", "#4E79A7", "o", 0.18),
        ("consensus_stable_yield", "Consensus", "#3A9D78", "s", 0.06),
        ("audit_view_stable_yield", "Audit view", "#E47D37", "D", -0.06),
        ("source_uncertain_fraction", "Source-uncertain", "#8B2D2D", "x", -0.18),
    ]
    for column, label, color, marker, offset in point_specs:
        kwargs = {"linewidth": 1.25} if marker == "x" else {"edgecolor": "white", "linewidth": 0.4}
        ax.scatter(
            screen[column], y + offset, color=color, marker=marker, s=30,
            label=label, zorder=3, **kwargs,
        )
    for yi, lo, hi in zip(y, screen["audit_view_stable_yield"], screen["mp_native_stable_yield"]):
        ax.plot([lo, hi], [yi - 0.06, yi + 0.18], color="#B7BDC4", linewidth=1.15, zorder=1)
    ax.set_yticks(y, names)
    ax.set_xlim(0.20, 0.44)
    ax.set_xlabel("Fraction of exact-matched candidates")
    ax.set_title("Exact-matched screeners", pad=7, fontweight="normal")
    clean_axis(ax, "x")
    panel_label(ax, "a")

    generated = unsupported[unsupported["pipeline_type"].isin(["true_generator", "available_crystal_generation_pipeline"])].copy()
    preferred = ["MatterGen_hf_base_smoke_unconditional", "MatterGen_pilot_5k_public_safe_formulas", "PGCGM_public_safe_generated_pool"]
    generated = generated.set_index("pipeline_name").reindex(preferred).dropna(subset=["candidate_n"]).reset_index()
    names = ["MatterGen\nsmoke", "MatterGen\nformula pool", "PGCGM\npool"]
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
    ax.set_yticks(y, names, fontsize=6.8)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Candidate-pool fraction")
    ax.set_title("Generated-pool support", pad=7, fontweight="normal")
    for yi, formula in zip(y, generated["formula_only_overlap_fraction"]):
        if formula >= 0.025:
            ax.text(
                formula + 0.014, yi, f"{100*formula:.1f}% formula-only",
                ha="left", va="center", fontsize=6.5, color="#765213", fontweight="bold",
            )
    clean_axis(ax, "x")
    panel_label(ax, "b")

    handles = [
        Line2D([0], [0], color="#4E79A7", marker="o", linewidth=0, markersize=4.5, label="MP-native"),
        Line2D([0], [0], color="#3A9D78", marker="s", linewidth=0, markersize=4.5, label="Consensus"),
        Line2D([0], [0], color="#E47D37", marker="D", linewidth=0, markersize=4.5, label="Audit view"),
        Line2D([0], [0], color="#8B2D2D", marker="x", linewidth=0, markersize=5.0, label="Source-uncertain"),
        Patch(facecolor="#F2BE5C", edgecolor="none", label="Formula-only"),
        Patch(facecolor="#B9BDC2", edgecolor="none", label="Unmatched"),
    ]
    fig.legend(handles, [handle.get_label() for handle in handles], loc="lower center", bbox_to_anchor=(0.52, 0.012), ncol=6, columnspacing=0.82, handletextpad=0.38, handlelength=1.3)
    fig.subplots_adjust(bottom=0.22, top=0.89, left=0.12, right=0.99)
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
    # A compact TOC graphic must keep every label inside the fixed 8 x 4 cm
    # canvas.  The short in-axis title replaces an overflow-prone page title.
    ax.set_xlim(0, 12_500)
    ax.set_xticks([0, 4_000, 8_000, 12_000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: "0" if x == 0 else f"{int(x / 1000)}k"))
    ax.set_ylim(0.15, 0.70)
    ax.set_xlabel("Candidates evaluated", labelpad=1.5)
    ax.set_ylabel("Stable yield", labelpad=1.5)
    ax.set_title("One ranking, multiple label views", fontsize=6.6, pad=2.0, fontweight="bold")
    ax.tick_params(labelsize=5.1, pad=1.3)
    ax.legend(loc="upper right", fontsize=4.6, handlelength=2.1, labelspacing=0.38, borderaxespad=0.55)
    clean_axis(ax)
    fig.subplots_adjust(left=0.18, right=0.96, bottom=0.23, top=0.88)
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
    (out / "toc_text.txt").write_text("Source-aware label views turn a fixed crystal ranking into distinct discovery curves, making label provenance visible in stable-yield and recall estimates.\n")
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
