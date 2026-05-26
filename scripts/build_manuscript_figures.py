from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
FULL_OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
BENCH_OUT = ROOT / "outputs" / "milestones" / "benchmark_impact_label_source_choice"
MODEL_OUT = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check"
FIG_DIR = ROOT / "manuscript" / "figures"


COLORS = {
    "ink": "#252A32",
    "muted": "#68717D",
    "grid": "#E5E7EB",
    "mp": "#4C78A8",
    "alex": "#8E63A9",
    "stable": "#4F9F69",
    "unstable": "#8AA0B8",
    "discord": "#E56B2E",
    "discord_dark": "#8C3A12",
    "uncertain": "#F2B84B",
    "light_blue": "#DCEAF7",
    "light_green": "#E3F2E8",
    "light_orange": "#FCE3D5",
    "light_purple": "#ECE4F2",
    "light_gray": "#F2F4F7",
    "gray": "#B8BEC7",
    "dark_gray": "#606975",
}


def setup_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.3,
            "ytick.major.size": 2.3,
            "legend.frameon": False,
            "figure.dpi": 160,
        }
    )


def exact_binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    base = FIG_DIR / stem
    for suffix, kwargs in [
        (".svg", {}),
        (".pdf", {}),
        (".png", {"dpi": 600}),
        (".tiff", {"dpi": 600}),
    ]:
        fig.savefig(base.with_suffix(suffix), bbox_inches="tight", **kwargs)


def load_full_strict_matches() -> pd.DataFrame:
    df = pd.read_csv(FULL_OUT / "table_full_mp_alex_structure_matches.csv")
    strict = df[df["match_status"].eq("strict_structure_match")].copy()
    strict["mp_stable_exact"] = strict["mp_stable_exact"].astype(bool)
    strict["alex_stable_exact"] = strict["alex_stable_exact"].astype(bool)
    strict["discordant"] = strict["mp_stable_exact"].ne(strict["alex_stable_exact"])
    strict["abs_delta_mev"] = (strict["mp_e_above_hull"] - strict["alex_e_above_hull"]).abs() * 1000.0
    strict["min_abs_hull_mev"] = np.minimum(
        strict["mp_e_above_hull"].abs(), strict["alex_e_above_hull"].abs()
    ) * 1000.0
    return strict


def panel_label(ax: plt.Axes, label: str, x: float = -0.08, y: float = 1.04) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.5, fontweight="bold", va="bottom")


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = COLORS["dark_gray"]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.8,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def rounded_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str,
    fontsize: float = 6.5,
    text_color: str = COLORS["ink"],
    weight: str = "normal",
) -> FancyBboxPatch:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        linewidth=0.8,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        linespacing=1.12,
        fontweight=weight,
    )
    return box


def funnel_step(
    ax: plt.Axes,
    center_x: float,
    y: float,
    top_w: float,
    bottom_w: float,
    height: float,
    facecolor: str,
    edgecolor: str,
    title: str,
    count: str,
) -> None:
    pts = [
        (center_x - top_w / 2, y + height),
        (center_x + top_w / 2, y + height),
        (center_x + bottom_w / 2, y),
        (center_x - bottom_w / 2, y),
    ]
    ax.add_patch(Polygon(pts, closed=True, facecolor=facecolor, edgecolor=edgecolor, linewidth=0.8))
    ax.text(center_x, y + height * 0.62, title, ha="center", va="center", fontsize=6.3, color=COLORS["ink"])
    ax.text(center_x, y + height * 0.28, count, ha="center", va="center", fontsize=8.1, fontweight="bold", color=edgecolor)


def build_fig1() -> None:
    manual_fig = FIG_DIR / "fig.pdf"
    if manual_fig.exists():
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manual_fig, FIG_DIR / "fig1_pipeline.pdf")
        try:
            subprocess.run(
                ["pdftocairo", "-svg", str(manual_fig), str(FIG_DIR / "fig1_pipeline.svg")],
                check=True,
            )
            subprocess.run(
                ["pdftoppm", "-png", "-r", "600", "-singlefile", str(manual_fig), str(FIG_DIR / "fig1_pipeline")],
                check=True,
            )
            from PIL import Image

            png_path = FIG_DIR / "fig1_pipeline.png"
            with Image.open(png_path) as image:
                image.save(FIG_DIR / "fig1_pipeline.tiff", dpi=(600, 600), compression="tiff_lzw")
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        return

    fig, ax = plt.subplots(figsize=(7.25, 3.95))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    panels = {
        "a": (0.012, 0.045, 0.320, 0.900),
        "b": (0.348, 0.045, 0.320, 0.900),
        "c": (0.684, 0.045, 0.304, 0.900),
    }

    def xy(panel: str, x: float, y: float) -> tuple[float, float]:
        px, py, pw, ph = panels[panel]
        return px + x * pw, py + y * ph

    def wh(panel: str, w: float, h: float) -> tuple[float, float]:
        _, _, pw, ph = panels[panel]
        return w * pw, h * ph

    def ptext(
        panel: str,
        x: float,
        y: float,
        text: str,
        fontsize: float = 6.0,
        color: str = COLORS["ink"],
        weight: str = "normal",
        ha: str = "center",
        va: str = "center",
        rotation: float = 0,
        linespacing: float = 1.10,
    ) -> None:
        ax.text(
            *xy(panel, x, y),
            text,
            fontsize=fontsize,
            color=color,
            fontweight=weight,
            ha=ha,
            va=va,
            rotation=rotation,
            linespacing=linespacing,
        )

    def pbox(
        panel: str,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        facecolor: str,
        edgecolor: str,
        fontsize: float = 5.5,
        text_color: str = COLORS["ink"],
        weight: str = "normal",
        radius: float = 0.014,
        linewidth: float = 0.8,
    ) -> None:
        gx, gy = xy(panel, x, y)
        gw, gh = wh(panel, w, h)
        ax.add_patch(
            FancyBboxPatch(
                (gx, gy),
                gw,
                gh,
                boxstyle=f"round,pad=0.006,rounding_size={radius}",
                facecolor=facecolor,
                edgecolor=edgecolor,
                linewidth=linewidth,
            )
        )
        if text:
            ax.text(
                gx + gw / 2,
                gy + gh / 2,
                text,
                ha="center",
                va="center",
                fontsize=fontsize,
                color=text_color,
                fontweight=weight,
                linespacing=1.08,
            )

    def parrow(panel: str, start: tuple[float, float], end: tuple[float, float], color: str = COLORS["dark_gray"], scale: float = 12) -> None:
        ax.add_patch(
            FancyArrowPatch(
                xy(panel, *start),
                xy(panel, *end),
                arrowstyle="-|>",
                mutation_scale=scale,
                linewidth=0.9,
                color=color,
                shrinkA=1.5,
                shrinkB=1.5,
            )
        )

    def pcylinder(panel: str, x: float, y: float, w: float, h: float, edge: str, face: str, label: str) -> None:
        gx, gy = xy(panel, x, y)
        gw, gh = wh(panel, w, h)
        ell_h = gh * 0.23
        ax.add_patch(Rectangle((gx, gy + ell_h / 2), gw, gh - ell_h, facecolor=face, edgecolor=edge, linewidth=1.0))
        ax.add_patch(Ellipse((gx + gw / 2, gy + gh - ell_h / 2), gw, ell_h, facecolor=face, edgecolor=edge, linewidth=1.0))
        ax.add_patch(Ellipse((gx + gw / 2, gy + ell_h / 2), gw, ell_h, facecolor=face, edgecolor=edge, linewidth=1.0, alpha=0.85))
        ax.text(gx + gw * 0.50, gy + gh * 0.66, label, ha="center", va="center", fontsize=5.6, color=edge, fontweight="bold")
        pts = np.array(
            [
                [0.22, 0.34],
                [0.38, 0.48],
                [0.55, 0.36],
                [0.72, 0.50],
                [0.32, 0.66],
                [0.62, 0.68],
                [0.78, 0.32],
            ]
        )
        for i, j in [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (5, 3), (2, 6), (3, 6)]:
            ax.plot(gx + pts[[i, j], 0] * gw, gy + pts[[i, j], 1] * gh, color=edge, linewidth=0.55, alpha=0.75)
        ax.scatter(gx + pts[:, 0] * gw, gy + pts[:, 1] * gh, s=18, color=edge, edgecolors="white", linewidths=0.25, zorder=4)

    def phull(panel: str, x: float, y: float, w: float, h: float) -> None:
        gx, gy = xy(panel, x, y)
        gw, gh = wh(panel, w, h)
        curve_x = np.linspace(0.10, 0.92, 8)
        curve_y = 0.25 + 0.70 * (curve_x - 0.52) ** 2
        ax.fill_between(gx + curve_x * gw, gy + (curve_y + 0.07) * gh, gy + (curve_y + 0.17) * gh, color="#D8DDE3", alpha=0.75)
        ax.plot(gx + curve_x * gw, gy + curve_y * gh, color=COLORS["dark_gray"], linewidth=0.9)
        ax.scatter(gx + curve_x * gw, gy + curve_y * gh, s=14, color=COLORS["dark_gray"], zorder=3)
        for xx, yy, color in [(0.34, 0.36, COLORS["stable"]), (0.62, 0.33, COLORS["mp"]), (0.87, 0.55, COLORS["alex"])]:
            ax.scatter([gx + xx * gw], [gy + yy * gh], s=22, color=color, zorder=4)
        for xx, yy in [(0.18, 0.48), (0.27, 0.58), (0.46, 0.45), (0.72, 0.49), (0.82, 0.30)]:
            ax.scatter([gx + xx * gw], [gy + yy * gh], s=10, color="#9AA0A6", zorder=2)

    for label, (px, py, pw, ph) in panels.items():
        ax.add_patch(
            FancyBboxPatch(
                (px, py),
                pw,
                ph,
                boxstyle="round,pad=0.010,rounding_size=0.012",
                facecolor="white",
                edgecolor="#6B6B6B",
                linewidth=0.65,
            )
        )
        ax.text(px + 0.020 * pw, py + 0.955 * ph, label, fontsize=12, fontweight="bold", ha="left", va="center")

    # Panel a: denominator construction.
    ptext("a", 0.52, 0.955, "Full MP–Alexandria\nexact-match denominator", fontsize=7.4, weight="bold")
    pcylinder("a", 0.055, 0.570, 0.315, 0.285, COLORS["stable"], "#E5F3E9", "Alexandria v20")
    pcylinder("a", 0.055, 0.170, 0.315, 0.285, COLORS["mp"], "#E7EFF7", "Materials Project")
    ax.plot(*zip(xy("a", 0.370, 0.705), xy("a", 0.510, 0.705)), color=COLORS["stable"], linewidth=5, alpha=0.45, solid_capstyle="round")
    ax.plot(*zip(xy("a", 0.370, 0.325), xy("a", 0.510, 0.325)), color=COLORS["mp"], linewidth=5, alpha=0.45, solid_capstyle="round")
    funnel = [xy("a", 0.500, 0.810), xy("a", 0.965, 0.810), xy("a", 0.835, 0.425), xy("a", 0.760, 0.395), xy("a", 0.760, 0.235), xy("a", 0.690, 0.235), xy("a", 0.690, 0.395), xy("a", 0.615, 0.425)]
    ax.add_patch(Polygon(funnel, closed=True, facecolor="#F8F8F8", edgecolor=COLORS["dark_gray"], linewidth=0.9))
    for yy in [0.665, 0.535]:
        ax.plot([xy("a", 0.540, yy)[0], xy("a", 0.900, yy)[0]], [xy("a", 0, yy)[1], xy("a", 0, yy)[1]], color=COLORS["gray"], linewidth=0.55, linestyle=(0, (2, 2)))
    ptext("a", 0.735, 0.735, "MP-ID overlap\n43,984", fontsize=6.0, weight="bold")
    ptext("a", 0.735, 0.600, "MP queried\n43,169", fontsize=5.7)
    ptext("a", 0.735, 0.475, "strict matches\n43,139", fontsize=5.5, color=COLORS["stable"], weight="bold")
    parrow("a", (0.735, 0.680), (0.735, 0.635), COLORS["dark_gray"], scale=10)
    parrow("a", (0.735, 0.555), (0.735, 0.510), COLORS["dark_gray"], scale=10)
    parrow("a", (0.725, 0.235), (0.725, 0.120), COLORS["dark_gray"], scale=12)
    ptext("a", 0.905, 0.345, "815\nnot returned", fontsize=4.8)
    ptext("a", 0.905, 0.225, "30\nmismatches", fontsize=4.8)
    pbox("a", 0.510, 0.070, 0.440, 0.100, "Retained denominator\n43,139", COLORS["light_green"], COLORS["stable"], fontsize=7.0, text_color=COLORS["stable"], weight="bold")

    # Panel b: binary label outcomes.
    ptext("b", 0.505, 0.955, "Binary stability-label outcomes", fontsize=7.4, weight="bold")
    ptext("b", 0.355, 0.820, "Alexandria\nunstable", fontsize=5.8, weight="bold")
    ptext("b", 0.685, 0.820, "Alexandria\nstable", fontsize=5.8, weight="bold")
    ptext("b", 0.085, 0.620, "MP\nunstable", fontsize=5.8, weight="bold", rotation=90)
    ptext("b", 0.085, 0.365, "MP\nstable", fontsize=5.8, weight="bold", rotation=90)
    x0, y0, w, h = 0.145, 0.235, 0.790, 0.555
    cell_w, cell_h = w / 2, h / 2
    outcomes = [
        (0, 1, "24,835", "both unstable", COLORS["light_blue"], COLORS["mp"], "solid"),
        (1, 1, "1,432", "Alex stable only", COLORS["light_green"], COLORS["stable"], (0, (3, 2))),
        (0, 0, "3,628", "MP stable only", COLORS["light_orange"], COLORS["discord"], (0, (3, 2))),
        (1, 0, "13,244", "both stable", COLORS["light_purple"], COLORS["alex"], "solid"),
    ]
    for col, row, count, label, face, edge, linestyle in outcomes:
        x, y = x0 + col * cell_w, y0 + row * cell_h
        gx, gy = xy("b", x, y)
        gw, gh = wh("b", cell_w, cell_h)
        ax.add_patch(Rectangle((gx, gy), gw, gh, facecolor=face, edgecolor=edge, linewidth=0.9, linestyle=linestyle))
        ptext("b", x + cell_w / 2, y + cell_h * 0.60, count, fontsize=8.8, color=edge, weight="bold")
        ptext("b", x + cell_w / 2, y + cell_h * 0.38, label, fontsize=5.5)
    ptext("b", 0.505, 0.115, "Discordant: ", fontsize=6.8, weight="bold", ha="right")
    ptext("b", 0.510, 0.115, "5,060", fontsize=6.8, color=COLORS["discord"], weight="bold", ha="left")
    ptext("b", 0.620, 0.115, " / 43,139 (11.7%)", fontsize=6.8, weight="bold", ha="left")

    # Panel c: source-aware benchmark reporting.
    ptext("c", 0.520, 0.955, "Source-aware benchmark\nreporting", fontsize=7.4, weight="bold")
    pbox("c", 0.035, 0.365, 0.250, 0.285, "", "white", COLORS["gray"], linewidth=0.7)
    ptext("c", 0.160, 0.605, "Conventional\nbenchmark", fontsize=5.0, weight="bold")
    pbox("c", 0.065, 0.495, 0.190, 0.070, "stable", COLORS["light_green"], COLORS["stable"], fontsize=5.5, text_color=COLORS["stable"], weight="bold")
    pbox("c", 0.065, 0.400, 0.190, 0.070, "unstable", COLORS["light_blue"], COLORS["mp"], fontsize=5.5, text_color=COLORS["mp"], weight="bold")
    parrow("c", (0.305, 0.510), (0.365, 0.510), COLORS["dark_gray"], scale=13)
    pbox("c", 0.405, 0.295, 0.300, 0.430, "", "white", COLORS["gray"], linewidth=0.7)
    ptext("c", 0.555, 0.680, "Source-aware\nbenchmark", fontsize=5.0, weight="bold")
    pbox("c", 0.435, 0.545, 0.240, 0.070, "stable", COLORS["light_green"], COLORS["stable"], fontsize=5.2, text_color=COLORS["stable"], weight="bold")
    pbox("c", 0.435, 0.450, 0.240, 0.070, "unstable", COLORS["light_blue"], COLORS["mp"], fontsize=5.2, text_color=COLORS["mp"], weight="bold")
    pbox("c", 0.435, 0.345, 0.240, 0.085, "cross-source\nuncertain", COLORS["light_orange"], COLORS["discord"], fontsize=4.9, text_color=COLORS["alex"], weight="bold")
    phull("c", 0.700, 0.315, 0.280, 0.420)
    for y, color in [(0.580, COLORS["stable"]), (0.485, COLORS["mp"]), (0.385, COLORS["alex"])]:
        ax.plot([xy("c", 0.675, y)[0], xy("c", 0.845, y)[0]], [xy("c", 0, y)[1], xy("c", 0, y)[1]], color=color, linewidth=0.8, linestyle=(0, (3, 2)))
    ptext("c", 0.500, 0.110, "5 meV: lower burden     |     25 meV: more conservative", fontsize=4.9)

    save_figure(fig, "fig1_pipeline")
    plt.close(fig)


def build_fig2() -> None:
    full = load_full_strict_matches()
    baseline = float(full["discordant"].mean())

    compressed_bins = [
        ("<10", full["abs_delta_mev"].lt(10.0)),
        ("10-100", full["abs_delta_mev"].ge(10.0) & full["abs_delta_mev"].lt(100.0)),
        (">=100", full["abs_delta_mev"].ge(100.0)),
    ]
    bin_rows = []
    for label, mask in compressed_bins:
        sub = full[mask]
        n = len(sub)
        k = int(sub["discordant"].sum())
        lo, hi = exact_binomial_ci(k, n)
        bin_rows.append((label, n, k, k / n, lo, hi))

    thresholds = [5, 10, 25, 50, 100]
    flag_rows = []
    total = len(full)
    discordant_total = int(full["discordant"].sum())
    for threshold in thresholds:
        flagged = full["min_abs_hull_mev"].le(threshold)
        flagged_n = int(flagged.sum())
        captured = int((flagged & full["discordant"]).sum())
        flag_rows.append(
            {
                "threshold": threshold,
                "flagged_fraction": flagged_n / total,
                "discordant_fraction": captured / total,
                "concordant_flagged_fraction": (flagged_n - captured) / total,
                "unflagged_fraction": 1.0 - flagged_n / total,
                "flagged_n": flagged_n,
                "captured": captured,
                "outside_n": total - flagged_n,
            }
        )
    flag_df = pd.DataFrame(flag_rows)

    fig = plt.figure(figsize=(7.25, 4.45))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.22, 0.95], height_ratios=[1.0, 0.92], wspace=0.33, hspace=0.42)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    panel_label(ax_a, "a", -0.10, 1.02)
    x_mev = full["mp_e_above_hull"].to_numpy(dtype=float) * 1000.0
    y_mev = full["alex_e_above_hull"].to_numpy(dtype=float) * 1000.0
    discordant = full["discordant"].to_numpy(dtype=bool)
    cap = 120.0
    x_plot = np.clip(x_mev, 0.0, cap)
    y_plot = np.clip(y_mev, 0.0, cap)
    density_cmap = LinearSegmentedColormap.from_list("source_density", ["#F7F8FA", "#C8D3E1", "#617894"])
    hb = ax_a.hexbin(
        x_plot[~discordant],
        y_plot[~discordant],
        gridsize=46,
        extent=(0, cap, 0, cap),
        mincnt=1,
        bins="log",
        cmap=density_cmap,
        linewidths=0,
    )
    ax_a.scatter(
        x_plot[discordant],
        y_plot[discordant],
        s=5.0,
        color=COLORS["discord"],
        edgecolor=COLORS["discord_dark"],
        linewidth=0.12,
        alpha=0.55,
        zorder=3,
    )
    ax_a.axvline(0, color=COLORS["ink"], linewidth=1.0)
    ax_a.axhline(0, color=COLORS["ink"], linewidth=1.0)
    for threshold, ls, lw, alpha in [(5, "-", 0.55, 0.70), (25, "--", 0.55, 0.60)]:
        ax_a.axvline(threshold, color=COLORS["uncertain"], linestyle=ls, linewidth=lw, alpha=alpha)
        ax_a.axhline(threshold, color=COLORS["uncertain"], linestyle=ls, linewidth=lw, alpha=alpha)
    ax_a.axline((0, 0), slope=1, color=COLORS["muted"], linewidth=0.65, linestyle=":")
    ax_a.set_xlim(-2, cap + 2)
    ax_a.set_ylim(-2, cap + 2)
    ax_a.set_xlabel(r"Materials Project $e_{\mathrm{hull}}$ (meV atom$^{-1}$)")
    ax_a.set_ylabel(r"Alexandria $e_{\mathrm{hull}}$ (meV atom$^{-1}$)")
    ax_a.text(0.03, 0.97, "zero-threshold lines", transform=ax_a.transAxes, ha="left", va="top", fontsize=6.0)
    ax_a.text(0.03, 0.90, "5/25 meV uncertainty bands", transform=ax_a.transAxes, ha="left", va="top", fontsize=6.0, color="#9A6A00")
    ax_a.text(0.97, 0.04, "values >120 meV clipped to edge", transform=ax_a.transAxes, ha="right", va="bottom", fontsize=5.6, color=COLORS["muted"])
    ax_a.scatter([], [], s=14, color=COLORS["discord"], edgecolor=COLORS["discord_dark"], linewidth=0.2, label="discordant")
    ax_a.legend(loc="upper right", fontsize=6.0, handletextpad=0.4)
    cbar = fig.colorbar(hb, ax=ax_a, fraction=0.045, pad=0.02)
    cbar.set_label("concordant density", fontsize=5.8)
    cbar.ax.tick_params(labelsize=5.5, length=2)

    panel_label(ax_b, "b", -0.12, 1.06)
    labels = [row[0] for row in bin_rows]
    x = np.arange(len(labels))
    rates = np.array([row[3] for row in bin_rows])
    ci_lo = np.array([row[4] for row in bin_rows])
    ci_hi = np.array([row[5] for row in bin_rows])
    yerr = np.vstack([rates - ci_lo, ci_hi - rates])
    bar_colors = [
        mpl.colors.to_rgba(COLORS["mp"], 0.72),
        mpl.colors.to_rgba(COLORS["discord"], 0.78),
        mpl.colors.to_rgba(COLORS["discord"], 0.58),
    ]
    ax_b.bar(x, rates, color=bar_colors, width=0.62)
    ax_b.errorbar(x, rates, yerr=yerr, fmt="none", ecolor=COLORS["ink"], elinewidth=0.7, capsize=2)
    ax_b.axhline(baseline, color=COLORS["dark_gray"], linestyle="--", linewidth=0.8)
    ax_b.text(2.35, baseline + 0.008, "baseline 11.7%", ha="right", va="bottom", fontsize=5.8, color=COLORS["dark_gray"])
    ax_b.set_xticks(x, labels)
    ax_b.set_ylim(0, 0.38)
    ax_b.set_ylabel("Discordance fraction")
    ax_b.set_xlabel(r"$|\Delta e|$ bin (meV atom$^{-1}$)")
    for i, (_, n, k, rate, _, hi) in enumerate(bin_rows):
        ax_b.text(i, hi + 0.015, f"{k}/{n}", ha="center", va="bottom", fontsize=5.7)

    panel_label(ax_c, "c", -0.12, 1.06)
    x = np.arange(len(flag_df))
    ax_c.bar(x, flag_df["discordant_fraction"], color=COLORS["discord"], width=0.64, label="discordant captured")
    ax_c.bar(
        x,
        flag_df["concordant_flagged_fraction"],
        bottom=flag_df["discordant_fraction"],
        color=COLORS["uncertain"],
        alpha=0.75,
        width=0.64,
        label="concordant flagged",
    )
    ax_c.bar(
        x,
        flag_df["unflagged_fraction"],
        bottom=flag_df["flagged_fraction"],
        color="white",
        edgecolor=COLORS["gray"],
        linewidth=0.6,
        width=0.64,
        label="unflagged",
    )
    ax_c.set_ylim(0, 1.02)
    ax_c.set_xticks(x, [str(v) for v in thresholds])
    ax_c.set_ylabel("Fraction of denominator")
    ax_c.set_xlabel(r"Either-source threshold (meV atom$^{-1}$)")
    for i, row in enumerate(flag_df.itertuples(index=False)):
        ax_c.text(i, row.flagged_fraction + 0.035, f"{row.flagged_fraction:.1%}", ha="center", va="bottom", fontsize=5.6)
    ax_c.text(
        0.02,
        0.97,
        "mechanical capture:\none source clipped to 0",
        transform=ax_c.transAxes,
        ha="left",
        va="top",
        fontsize=5.9,
        color=COLORS["discord_dark"],
        bbox={"boxstyle": "round,pad=0.20", "facecolor": "white", "edgecolor": COLORS["discord"], "linewidth": 0.45},
    )
    ax_c.text(0.02, 0.75, "outside-flag\ndiscordance = 0", transform=ax_c.transAxes, ha="left", va="top", fontsize=5.8, color=COLORS["muted"])
    ax_c.legend(loc="upper left", bbox_to_anchor=(0.0, -0.34), ncol=2, fontsize=5.6, columnspacing=0.9, handlelength=1.1)

    save_figure(fig, "fig2_delta_e")
    plt.close(fig)


def build_fig3() -> None:
    oracle = pd.read_csv(BENCH_OUT / "table_perfect_source_labeler_cross_evaluation.csv")
    retention = pd.read_csv(BENCH_OUT / "table_conflict_excluded_denominator_metrics.csv")
    oracle_topk = pd.read_csv(BENCH_OUT / "table_source_native_ranking_topk_stable_yield.csv")
    precision = pd.read_csv(MODEL_OUT / "table_precision_at_k_source_sensitivity.csv")
    shifts = pd.read_csv(MODEL_OUT / "table_precision_shift_bootstrap.csv")
    topk = pd.read_csv(MODEL_OUT / "table_topk_discordance_decomposition.csv")
    scores = pd.read_csv(MODEL_OUT / "candidate_scores_chgnet_5000.csv")

    fig = plt.figure(figsize=(7.35, 5.65))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.05, 1.08], height_ratios=[1.0, 1.0], wspace=0.40, hspace=0.52)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    ax_d = fig.add_subplot(gs[1, 0])
    ax_e = fig.add_subplot(gs[1, 1])
    ax_f = fig.add_subplot(gs[1, 2])

    # Panel a: source-label oracle transfer as a metric slope plot.
    panel_label(ax_a, "a", -0.18, 1.04)
    mp_cross = oracle[
        oracle["predictor"].eq("perfect_MP_source_labeler")
        & oracle["evaluation_label_source"].eq("Alexandria_source_native_truth")
    ].iloc[0]
    retain = retention[retention["denominator"].eq("source_agreement_only_conflict_excluded")].iloc[0]
    ax_a.plot([0, 1], [1.0, float(mp_cross["f1"])], marker="o", color=COLORS["alex"], lw=1.35, ms=3.5, label="source-label oracle")
    ax_a.axhline(float(retain["n"]) / 43139.0, color=COLORS["dark_gray"], ls="--", lw=0.75)
    ax_a.text(1.02, float(mp_cross["f1"]), "0.840", ha="left", va="center", fontsize=5.8, color=COLORS["ink"])
    ax_a.text(0.52, float(retain["n"]) / 43139.0 + 0.012, "agreement retained 0.883", ha="center", va="bottom", fontsize=5.5, color=COLORS["dark_gray"])
    ax_a.annotate("-0.160 F1", xy=(0.83, 0.865), xytext=(0.46, 0.965), arrowprops={"arrowstyle": "->", "lw": 0.65, "color": COLORS["discord_dark"]}, fontsize=5.7, color=COLORS["discord_dark"])
    ax_a.set_xlim(-0.08, 1.14)
    ax_a.set_ylim(0.78, 1.025)
    ax_a.set_xticks([0, 1], ["source-native", "cross-source"])
    ax_a.set_ylabel("F1 / retained fraction")
    ax_a.grid(axis="y", color=COLORS["grid"], lw=0.55)
    ax_a.legend(loc="lower left", fontsize=5.4, handlelength=1.4)

    # Panel b: oracle top-K stable-yield curves.
    panel_label(ax_b, "b", -0.16, 1.04)
    oracle_styles = [
        ("MP_source_native_ehull_rank", "mp_stable_rate_at_K", "MP rank, MP labels", COLORS["mp"], "-"),
        ("MP_source_native_ehull_rank", "alex_stable_rate_at_K", "MP rank, Alex labels", COLORS["mp"], "--"),
        ("Alexandria_source_native_ehull_rank", "alex_stable_rate_at_K", "Alex rank, Alex labels", COLORS["alex"], "-"),
        ("Alexandria_source_native_ehull_rank", "mp_stable_rate_at_K", "Alex rank, MP labels", COLORS["alex"], "--"),
    ]
    for ranking, col, label, color, ls in oracle_styles:
        sub = oracle_topk[oracle_topk["ranking"].eq(ranking)].sort_values("K")
        ax_b.plot(sub["K"], sub[col], marker="o", ms=2.6, lw=0.9, color=color, ls=ls, label=label)
    ax_b.set_xscale("log")
    ax_b.set_ylim(0.74, 1.02)
    ax_b.set_xlabel("Top K under source-native hull ranking")
    ax_b.set_ylabel("Stable fraction")
    ax_b.grid(axis="y", color=COLORS["grid"], lw=0.55)
    ax_b.legend(loc="lower left", fontsize=5.1, handlelength=1.7)

    # Panel c: CHGNet precision@K line plot for all archived K values.
    panel_label(ax_c, "c", -0.16, 1.04)
    for label_source, label, color in [
        ("mp_stable", "MP labels", COLORS["mp"]),
        ("alex_stable", "Alex labels", COLORS["alex"]),
        ("agreement_stable", "agreement-only", COLORS["stable"]),
    ]:
        sub = precision[precision["label_source"].eq(label_source)].sort_values("K")
        ax_c.plot(sub["K"], sub["precision_at_K"], marker="o", lw=1.0, ms=2.8, color=color, label=label)
    ax_c.set_xscale("log")
    ax_c.set_ylim(0.18, 0.40)
    ax_c.set_xlabel("Top K under fixed CHGNet ranking")
    ax_c.set_ylabel("Precision@K")
    ax_c.grid(axis="y", color=COLORS["grid"], lw=0.55)
    ax_c.text(300, 0.366, "+4.3 pp", ha="center", va="bottom", fontsize=5.8, color=COLORS["discord_dark"])
    ax_c.text(500, 0.338, "+3.6 pp", ha="center", va="bottom", fontsize=5.8, color=COLORS["discord_dark"])
    ax_c.legend(loc="upper right", fontsize=5.2, handlelength=1.7)

    # Panel d: MP-minus-Alex precision-shift intervals.
    panel_label(ax_d, "d", -0.18, 1.04)
    sh = shifts.sort_values("K")
    y = np.arange(len(sh))
    ax_d.axvline(0, color=COLORS["dark_gray"], ls="--", lw=0.7)
    ax_d.errorbar(
        sh["observed_mp_minus_alex_precision_shift"] * 100,
        y,
        xerr=[
            (sh["observed_mp_minus_alex_precision_shift"] - sh["bootstrap_ci_low"]) * 100,
            (sh["bootstrap_ci_high"] - sh["observed_mp_minus_alex_precision_shift"]) * 100,
        ],
        fmt="o",
        ms=3.1,
        lw=0.8,
        color=COLORS["discord"],
        ecolor=COLORS["discord"],
        capsize=2,
    )
    ax_d.set_yticks(y, [f"K={int(k)}" for k in sh["K"]])
    ax_d.set_xlabel("MP - Alex precision shift (pp)")
    ax_d.set_xlim(-6, 11)
    ax_d.grid(axis="x", color=COLORS["grid"], lw=0.55)
    ax_d.invert_yaxis()

    # Panel e: score distribution by source-label class.
    panel_label(ax_e, "e", -0.16, 1.04)
    cls = np.select(
        [
            scores["mp_stable"].astype(bool) & scores["alex_stable"].astype(bool),
            scores["mp_stable"].astype(bool) & ~scores["alex_stable"].astype(bool),
            ~scores["mp_stable"].astype(bool) & scores["alex_stable"].astype(bool),
            ~scores["mp_stable"].astype(bool) & ~scores["alex_stable"].astype(bool),
        ],
        ["both stable", "MP only", "Alex only", "both unstable"],
        default="other",
    )
    scores = scores.assign(label_class=cls)
    order = ["both stable", "MP only", "Alex only", "both unstable"]
    class_colors = [COLORS["stable"], COLORS["discord"], COLORS["alex"], COLORS["unstable"]]
    rng = np.random.default_rng(20260525)
    data = [scores.loc[scores["label_class"].eq(name), "score"].to_numpy() for name in order]
    box = ax_e.boxplot(data, positions=np.arange(len(order)), widths=0.42, patch_artist=True, showfliers=False, medianprops={"color": COLORS["ink"], "lw": 0.8})
    for patch, color in zip(box["boxes"], class_colors, strict=False):
        patch.set_facecolor(mpl.colors.to_rgba(color, 0.18))
        patch.set_edgecolor(color)
        patch.set_linewidth(0.7)
    for i, (name, color) in enumerate(zip(order, class_colors, strict=False)):
        vals = scores.loc[scores["label_class"].eq(name), "score"].to_numpy()
        if len(vals) > 900:
            vals = rng.choice(vals, size=900, replace=False)
        xj = rng.normal(i, 0.055, size=len(vals))
        ax_e.scatter(xj, vals, s=1.2, alpha=0.13, color=color, linewidths=0)
    ax_e.set_xticks(np.arange(len(order)), ["both\nstable", "MP\nonly", "Alex\nonly", "both\nunstable"])
    ax_e.set_ylabel("CHGNet ranking score")
    ax_e.set_ylim(-0.25, 4.65)
    ax_e.grid(axis="y", color=COLORS["grid"], lw=0.55)

    # Panel f: top-K source-label composition as a stacked fraction plot.
    panel_label(ax_f, "f", -0.16, 1.04)
    parts = [
        ("both stable", "both_stable_n", COLORS["stable"]),
        ("MP only", "mp_only_stable_n", COLORS["discord"]),
        ("Alex only", "alex_only_stable_n", COLORS["alex"]),
        ("both unstable", "both_unstable_n", COLORS["unstable"]),
    ]
    top = topk.sort_values("K").reset_index(drop=True)
    y = np.arange(len(top))
    left = np.zeros(len(top))
    for label, col, color in parts:
        vals = top[col].to_numpy(dtype=float) / top["K"].to_numpy(dtype=float)
        ax_f.barh(y, vals, left=left, height=0.62, color=mpl.colors.to_rgba(color, 0.76), label=label)
        left += vals
    ax_f.set_yticks(y, [str(int(k)) for k in top["K"]])
    ax_f.set_xlabel("Fraction of top K")
    ax_f.set_ylabel("Top K")
    ax_f.set_xlim(0, 1)
    ax_f.invert_yaxis()
    ax_f.legend(loc="lower center", bbox_to_anchor=(0.5, -0.42), ncol=2, fontsize=5.0, columnspacing=0.8, handlelength=1.0)

    save_figure(fig, "fig3_benchmark_impact")
    plt.close(fig)


def build_fig4() -> None:
    chem = pd.read_csv(FULL_OUT / "table_major_revision_chemistry_stratified_discordance.csv")
    baseline = 5060 / 43139
    labels = {
        ("element_count", "unary"): "Unary",
        ("element_count", "binary"): "Binary",
        ("element_count", "ternary"): "Ternary",
        ("element_count", "quaternary_plus"): "Quaternary+",
        ("contains_transition_metal", "True"): "Transition metal",
        ("contains_transition_metal", "False"): "No transition metal",
        ("contains_lanthanide", "True"): "Lanthanide",
        ("contains_lanthanide", "False"): "No lanthanide",
        ("contains_oxygen", "True"): "Oxygen",
        ("contains_oxygen", "False"): "No oxygen",
        ("contains_halogen", "True"): "Halogen",
        ("contains_halogen", "False"): "No halogen",
    }
    order = [
        ("element_count", "unary"),
        ("element_count", "binary"),
        ("element_count", "ternary"),
        ("element_count", "quaternary_plus"),
        ("contains_transition_metal", "True"),
        ("contains_transition_metal", "False"),
        ("contains_lanthanide", "True"),
        ("contains_lanthanide", "False"),
        ("contains_oxygen", "True"),
        ("contains_oxygen", "False"),
        ("contains_halogen", "True"),
        ("contains_halogen", "False"),
    ]
    rows = []
    for group_type, group in order:
        row = chem[chem["group_type"].eq(group_type) & chem["group"].astype(str).eq(group)].iloc[0]
        lo, hi = exact_binomial_ci(int(row["discordant"]), int(row["n"]))
        rows.append(
            {
                "label": labels[(group_type, group)],
                "n": int(row["n"]),
                "rate": float(row["discordance_rate"]),
                "lo": lo,
                "hi": hi,
                "mp_only": int(row["mp_stable_alex_unstable"]),
                "alex_only": int(row["mp_unstable_alex_stable"]),
                "median_delta": float(row["median_abs_delta_mev"]),
                "p90_delta": float(row["p90_abs_delta_mev"]),
            }
        )
    data = pd.DataFrame(rows)

    fig = plt.figure(figsize=(7.25, 4.75))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.12, 1.0], height_ratios=[1.0, 0.9], wspace=0.34, hspace=0.44)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    panel_label(ax_a, "a", -0.16, 1.02)
    y = np.arange(len(data))[::-1]
    rates = data["rate"].to_numpy() * 100
    xerr = np.vstack([(data["rate"] - data["lo"]).to_numpy() * 100, (data["hi"] - data["rate"]).to_numpy() * 100])
    colors = [COLORS["discord"] if rate > baseline * 100 else COLORS["mp"] for rate in rates]
    ax_a.axvline(baseline * 100, color=COLORS["dark_gray"], ls="--", lw=0.8)
    ax_a.errorbar(rates, y, xerr=xerr, fmt="none", ecolor=COLORS["gray"], elinewidth=0.75, capsize=1.8, zorder=1)
    ax_a.scatter(rates, y, s=20, c=colors, edgecolors="white", linewidths=0.45, zorder=2)
    ax_a.set_yticks(y, data["label"])
    ax_a.set_xlabel("Discordance rate (%)")
    ax_a.set_xlim(4, 19)
    ax_a.grid(axis="x", color=COLORS["grid"], lw=0.55)
    ax_a.text(baseline * 100 + 0.25, y.max() + 0.42, "full baseline 11.7%", fontsize=5.6, color=COLORS["dark_gray"], ha="left")
    for yi, n in zip(y, data["n"], strict=False):
        ax_a.text(18.9, yi, f"n={n:,}", ha="right", va="center", fontsize=5.2, color=COLORS["muted"])

    panel_label(ax_b, "b", -0.16, 1.05)
    idx = np.arange(len(data))
    mp_frac = data["mp_only"].to_numpy() / (data["mp_only"].to_numpy() + data["alex_only"].to_numpy())
    alex_frac = 1 - mp_frac
    ax_b.bar(idx, mp_frac, color=mpl.colors.to_rgba(COLORS["discord"], 0.78), width=0.72, label="MP stable only")
    ax_b.bar(idx, alex_frac, bottom=mp_frac, color=mpl.colors.to_rgba(COLORS["alex"], 0.72), width=0.72, label="Alex stable only")
    ax_b.axhline(0.5, color=COLORS["dark_gray"], ls="--", lw=0.65)
    ax_b.set_ylim(0, 1)
    ax_b.set_ylabel("Share of discordant labels")
    ax_b.set_xticks(idx, [str(i + 1) for i in idx], fontsize=5.5)
    ax_b.grid(axis="y", color=COLORS["grid"], lw=0.55)
    ax_b.legend(loc="upper center", bbox_to_anchor=(0.55, 1.18), ncol=2, fontsize=5.2, handlelength=1.0, columnspacing=0.9)
    ax_b.text(0.01, -0.26, "Index follows panel a order", transform=ax_b.transAxes, fontsize=5.4, color=COLORS["muted"], ha="left")

    panel_label(ax_c, "c", -0.16, 1.05)
    ax_c.scatter(data["median_delta"], data["p90_delta"], s=np.sqrt(data["n"]) * 1.4, c=colors, alpha=0.78, edgecolors="white", linewidths=0.45)
    for _, row in data.iterrows():
        if row["label"] in {"Halogen", "Oxygen", "Unary", "Quaternary+"}:
            ax_c.text(row["median_delta"] + 0.10, row["p90_delta"] + 0.35, row["label"], fontsize=5.2, color=COLORS["ink"])
    ax_c.set_xlabel("Median |Delta e| (meV atom$^{-1}$)")
    ax_c.set_ylabel("P90 |Delta e| (meV atom$^{-1}$)")
    ax_c.set_xlim(-0.2, 5.6)
    ax_c.set_ylim(17, 33.5)
    ax_c.grid(color=COLORS["grid"], lw=0.55)

    save_figure(fig, "fig4_chemical_stratification")
    plt.close(fig)


def main() -> None:
    setup_style()
    build_fig1()
    build_fig2()
    build_fig3()
    build_fig4()
    print(f"Wrote manuscript figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
