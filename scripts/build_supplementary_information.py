#!/usr/bin/env python3
"""Generate the complete Digital Discovery Supplementary Information PDF."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sourceaware.dd_submission import DEFAULT_OUT, DEFAULT_PHASE1, DEFAULT_PHASE2, REAL_MODELS, rank_flip_normalisation


def tex_escape(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "--"
    if isinstance(value, (float, np.floating)):
        if abs(value) < 1e-3 and value != 0:
            return f"{value:.2e}"
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    text = str(value)
    text = text.replace("–", "--").replace("—", "---").replace("≤", "$\\leq$").replace("≥", "$\\geq$")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_\allowbreak{}",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    # Preserve math tokens inserted above.
    math_tokens = {}
    for idx, token in enumerate(re.findall(r"\$[^$]+\$", text)):
        key = f"@@MATH{idx}@@"
        math_tokens[key] = token
        text = text.replace(token, key, 1)
    for old, new in replacements.items():
        text = text.replace(old, new)
    for key, token in math_tokens.items():
        text = text.replace(key, token)
    return text


def longtable(df: pd.DataFrame, columns: list[str], headers: list[str], caption: str, label: str, align: str | None = None) -> str:
    data = df.loc[:, columns].copy()
    if align is None:
        align = "l" * len(columns)
    header = " & ".join(tex_escape(x) for x in headers) + r" \\"
    rows = [" & ".join(tex_escape(value) for value in row) + r" \\" for row in data.itertuples(index=False, name=None)]
    return "\n".join(
        [
            r"\begin{landscape}",
            r"\tiny\setlength{\tabcolsep}{2.2pt}",
            rf"\begin{{longtable}}{{@{{}}{align}@{{}}}}",
            rf"\caption{{{caption}}}\label{{{label}}}\\",
            r"\toprule",
            header,
            r"\midrule",
            r"\endfirsthead",
            rf"\multicolumn{{{len(columns)}}}{{l}}{{\textit{{Table continued}}}}\\",
            r"\toprule",
            header,
            r"\midrule",
            r"\endhead",
            r"\midrule",
            rf"\multicolumn{{{len(columns)}}}{{r}}{{\textit{{Continued on next page}}}}\\",
            r"\endfoot",
            r"\bottomrule",
            r"\endlastfoot",
            *rows,
            r"\end{longtable}",
            r"\end{landscape}",
        ]
    )


def manifest_table(phase1: Path, phase2: Path, dd_out: Path) -> pd.DataFrame:
    rows = []
    for phase, path in [("phase1_v2", phase1 / "manifest_phase1_v2.json"), ("phase2_v1", phase2 / "manifest_phase2_v1.json")]:
        payload = json.loads(path.read_text())
        for row in payload["files"]:
            rows.append(
                {
                    "phase": phase,
                    "path": row.get("path"),
                    "rows": row.get("rows"),
                    "columns": row.get("columns"),
                    "bytes": row.get("bytes"),
                    "sha256": row.get("sha256", "")[:16],
                }
            )
    for path in sorted(dd_out.rglob("*")):
        if path.is_file():
            rows.append(
                {
                    "phase": "dd_submission_v2",
                    "path": str(path.relative_to(REPO)),
                    "rows": None,
                    "columns": None,
                    "bytes": path.stat().st_size,
                    "sha256": "see submission manifest",
                }
            )
    return pd.DataFrame(rows)


def build_tex(phase1: Path, phase2: Path, dd_out: Path, manuscript_dir: Path) -> str:
    inventory = pd.read_csv(phase2 / "model_scores" / "model_score_inventory.csv")
    metrics = pd.read_csv(phase2 / "model_metrics" / "metrics_by_model_label_view.csv")
    topk = pd.read_csv(phase2 / "model_metrics" / "topk_by_model_label_view.csv")
    metric_ci = pd.read_csv(phase2 / "model_metrics" / "metrics_by_model_label_view_bootstrap.csv")
    topk_ci = pd.read_csv(phase2 / "model_metrics" / "topk_by_model_label_view_bootstrap.csv")
    primary_views = ["mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "consensus", "audit_view"]
    metric_ci_primary = metric_ci[
        metric_ci["denominator"].eq("D5_family_complete")
        & metric_ci["model_name"].isin(REAL_MODELS)
        & metric_ci["label_view"].isin(primary_views)
    ].copy()
    topk_ci_primary = topk_ci[
        topk_ci["denominator"].eq("D5_family_complete")
        & topk_ci["model_name"].isin(REAL_MODELS)
        & topk_ci["label_view"].isin(primary_views)
        & topk_ci["metric"].astype(str).str.startswith(("stable_yield@", "uncertain_fraction@"))
    ].copy()
    rank_audit = pd.read_csv(phase2 / "rank_inversions" / "real_model_rank_claim_audit.csv")
    tie = pd.read_csv(REPO / "outputs" / "milestones" / "official_alexandria_pbe_feasibility" / "table_official_alexandria_pbe_multiple_match_tie_break_sensitivity.csv")
    chem = pd.read_csv(REPO / "outputs" / "milestones" / "official_alexandria_pbe_extension" / "table_official_alexandria_chemistry_stratified_bootstrap.csv")
    candidate_match = pd.read_csv(phase2 / "generative" / "generated_candidate_match_quality_by_pipeline.csv")
    candidate_prov = pd.read_csv(phase2 / "generative" / "generated_candidate_artifact_provenance.csv")
    candidate_prov["sha256"] = candidate_prov["sha256"].fillna("").astype(str).str.slice(0, 16)
    candidate_inventory = pd.read_csv(phase2 / "generative" / "generated_candidate_inventory.csv")
    claims = pd.read_csv(phase2 / "phase2_claim_support_matrix.csv")
    d3 = pd.read_parquet(phase1 / "denominator_d3_jarvis_overlap.parquet")
    jarvis_summary = (
        d3.groupby(["match_status", "multiple_match_status"], dropna=False)
        .size().rename("n").reset_index().sort_values("n", ascending=False)
    )
    jarvis_top = d3[d3["jarvis_match_count"].fillna(0).gt(1)][["row_id", "formula", "chemical_system", "jarvis_id", "jarvis_match_count"]].sort_values("jarvis_match_count", ascending=False).head(100)
    manifest = manifest_table(phase1, phase2, dd_out)
    rank_norm = rank_flip_normalisation(phase2)

    preamble = r"""\documentclass[10pt]{article}
\usepackage[margin=1.7cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{charter}
\usepackage{booktabs,longtable,array,pdflscape,multirow}
\usepackage[super,sort&compress,comma]{natbib}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\setlength{\LTpre}{4pt}\setlength{\LTpost}{6pt}
\setlength{\emergencystretch}{2em}
\sloppy
\newcommand{\sourceaware}{SourceAware-Stability}
\title{Supplementary Information\\\large Source-aware stability labels reshape AI crystal-discovery benchmarks}
\author{Xinling Wen, Jiahao Zhang, Yawei Hou and Yu Chen}
\date{}
\begin{document}
\maketitle
\tableofcontents
\clearpage
"""
    parts = [preamble]
    parts.append(r"""\section{Scope and guardrails}
This Supplementary Information reports the complete frozen public-source evidence used for the Digital Discovery manuscript. It does not use NMI-upgrade scaffold outputs as scientific evidence. No homogeneous DFT referee truth labels, generated-material validation or complete full-source-union hull are claimed. Consensus, common-pool, source-union and audit labels remain benchmark diagnostics rather than physical truth.

The primary exact SourceAware model comparison contains only ALIGNN-FF, CHGNet, M3GNet and MACE-MP. Other entries are external WBM context, artifact inventory, baselines or oracle diagnostics. Scores are diagnostic rankings and are not calibrated source-comparable hull distances.
""")
    parts.append(r"\section{Full model inventory}")
    parts.append(longtable(
        inventory,
        ["model_name", "model_family", "model_role", "coverage_n", "missing_n", "score_status", "source_of_score", "whether_calibrated_energy", "whether_hull_distance", "include_in_primary_leaderboard"],
        ["Model", "Family", "Role", "Coverage", "Missing", "Status", "Score source", "Calibrated energy", "Hull distance", "Primary"],
        "Complete model and diagnostic inventory. Entries without exact SourceAware row mapping are not used in primary label-view claims.",
        "tab:full-model-inventory",
        "p{2.3cm}p{2.0cm}p{1.8cm}rrp{2.2cm}p{4.2cm}p{1.5cm}p{1.5cm}p{1.3cm}",
    ))
    parts.append(r"\section{All label-view metrics}")
    parts.append(r"Table~\ref{tab:all-metrics} reproduces every row of the frozen model-by-label-view metric table, including baselines and non-evaluable source-union status rows. Primary manuscript claims use only the four real models and exact D5 rows.")
    parts.append(longtable(
        metrics,
        ["denominator", "model_name", "label_view", "n", "positive_rate", "metric_status", "f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"],
        ["Denominator", "Model", "Label view", "$n$", "Positive rate", "Status", "F1", "Precision", "Recall", "Balanced accuracy", "AUROC", "AUPRC"],
        "Complete model-by-label-view metrics.", "tab:all-metrics", "lllrrlrrrrrr",
    ))
    parts.append(r"\section{All top-$K$ tables}")
    parts.append(longtable(
        topk,
        ["denominator", "model_name", "label_view", "K", "K_effective", "n_ranked", "stable_n", "stable_yield_at_k", "recall_at_k", "uncertain_fraction_at_k", "DAF_at_k", "metric_status"],
        ["Denominator", "Model", "View", "$K$", "$K_{eff}$", "Ranked", "Stable", "Yield", "Recall", "Uncertain", "DAF", "Status"],
        "Complete frozen top-$K$ table for all models, views, denominators and budgets.", "tab:all-topk", "lllrrrrrrrrl",
    ))
    parts.append(r"\section{Uncertainty intervals}")
    parts.append(r"""The frozen interval tables use deterministic binomial approximations. The near-threshold rolling analysis in the main manuscript instead uses Wilson 95\% intervals with a minimum window count of 1,000. Its metadata explicitly record a null bootstrap seed and zero iterations because no bootstrap is used. Chemistry-stratified analyses use chemical-system cluster bootstrap with 5,000 iterations and seed 20260705 (Table~\ref{tab:chemistry}).""")
    parts.append(longtable(
        metric_ci_primary,
        ["denominator", "model_name", "label_view", "metric", "value", "ci_low_95", "ci_high_95", "bootstrap_method"],
        ["Denominator", "Model", "View", "Metric", "Value", "95 percent low", "95 percent high", "Method"],
        "Primary exact real-model metric interval table. The complete interval CSV is included in the release.", "tab:metric-intervals", "llllrrrl",
    ))
    parts.append(longtable(
        topk_ci_primary,
        ["denominator", "model_name", "label_view", "K", "metric", "value", "ci_low_95", "ci_high_95", "ci_denominator_n", "metric_status"],
        ["Denominator", "Model", "View", "K", "Metric", "Value", "95 percent low", "95 percent high", "CI n", "Status"],
        "Primary exact real-model stable-yield and uncertain-fraction interval table. The complete interval CSV is included in the release.", "tab:topk-intervals", "lllrlrrrrl",
    ))
    parts.append(r"\section{Rank inversion definitions and normalisation}")
    parts.append(r"""A winner flip is a model-pair--metric comparison whose sign changes between two label views. The denominator is the number of available label-view pairs summed across model pairs and metrics. The aggregate diagnostic includes baselines and oracles and therefore is not primary real-model evidence. The real-model scope contains four models, six model pairs, 42 metrics and eight label views. Full-denominator classification metrics show no top-real-model inversion; budgeted stable-yield metrics are reported separately.""")
    parts.append(longtable(rank_norm, list(rank_norm.columns), [x.replace("_", " ") for x in rank_norm.columns], "Pairwise winner-flip normalisation.", "tab:rank-normalisation"))
    parts.append(longtable(
        rank_audit,
        ["denominator", "metric", "label_view_a", "label_view_b", "common_real_model_n", "real_model_rank_inversion_count", "top_real_model_a", "top_real_model_b", "top_real_model_inversion", "claim_interpretation"],
        ["Denominator", "Metric", "View A", "View B", "Models", "Pair flips", "Top A", "Top B", "Top flip", "Interpretation"],
        "Complete real-model rank audit. The 216 legacy lower-rank rows span three denominator variants and all metric families.", "tab:rank-audit", "llllrrllll",
    ))
    parts.append(r"\section{Matching and duplicate sensitivity}")
    parts.append(longtable(tie, list(tie.columns), [x.replace("_", " ") for x in tie.columns], "Official Alexandria multiple-match tie-break sensitivity.", "tab:tie-break"))
    parts.append(longtable(
        candidate_match,
        ["pipeline_name", "pipeline_type", "candidate_n", "exact_sourceaware_match_n", "formula_only_overlap_n", "no_formula_overlap_n", "duplicate_n", "near_threshold_25meV_n", "label_assignment_policy"],
        ["Pipeline", "Type", "Candidates", "Exact", "Formula-only", "Unmatched", "Duplicates", "Near 25 meV", "Policy"],
        "Candidate matching and duplicate sensitivity. Formula-only overlap never creates a stability label.", "tab:candidate-matching", "llrrrrrrl",
    ))
    parts.append(r"\section{Chemistry stratification}")
    parts.append(longtable(
        chem,
        ["cutoff_mev_atom", "source_pair", "stratum_type", "stratum", "n", "chemical_system_n", "conflict_n", "conflict_fraction", "cluster_bootstrap_ci_low", "cluster_bootstrap_ci_high", "n_bootstrap", "bootstrap_seed"],
        ["Cutoff (meV)", "Source pair", "Stratum type", "Stratum", "$n$", "Systems", "Conflicts", "Fraction", "CI low", "CI high", "Bootstraps", "Seed"],
        "Chemistry-stratified source conflict with chemical-system cluster-bootstrap intervals.", "tab:chemistry", "rlllrrrrrrrr",
    ))
    parts.append(r"\section{JARVIS portability}")
    parts.append(longtable(jarvis_summary, list(jarvis_summary.columns), ["Match status", "Multiplicity", "Rows"], "JARVIS exact-structure portability summary.", "tab:jarvis-summary"))
    parts.append(longtable(jarvis_top, list(jarvis_top.columns), ["Row ID", "Formula", "Chemical system", "JARVIS IDs", "Match count"], "Top 100 JARVIS multiple-match rows; multiplicity is reported rather than silently tie-broken.", "tab:jarvis-multiple", "p{2.4cm}p{2.4cm}p{3cm}p{13cm}r"))
    parts.append(r"\section{Candidate provenance}")
    parts.append(longtable(
        candidate_inventory,
        [c for c in ["pipeline_name", "pipeline_type", "candidate_n", "status", "source", "claim_scope"] if c in candidate_inventory.columns],
        [c.replace("_", " ") for c in [c for c in ["pipeline_name", "pipeline_type", "candidate_n", "status", "source", "claim_scope"] if c in candidate_inventory.columns]],
        "Generated and screened candidate inventory.", "tab:candidate-inventory", "p{4.2cm}p{3.2cm}rp{4.8cm}p{7.8cm}",
    ))
    parts.append(longtable(
        candidate_prov,
        ["pipeline_name", "artifact_role", "artifact_kind", "path_scope", "exists", "row_count", "structure_count", "sha256", "label_assignment_status"],
        ["Pipeline", "Role", "Artifact", "Scope", "Exists", "Rows", "Structures", "SHA256", "Label status"],
        "Candidate artifact provenance. Private raw artifacts are represented only by redacted hashes/counts.", "tab:candidate-provenance", "p{3.5cm}p{2.8cm}p{2.8cm}p{2cm}lrrp{2.4cm}p{5cm}",
    ))
    parts.append(r"\section{Claim support matrix}")
    parts.append(longtable(
        claims,
        ["claim_id", "claim_text", "support_status", "primary_evidence", "manuscript_safe_language", "overclaim_to_avoid"],
        ["Claim ID", "Claim", "Status", "Evidence", "Safe language", "Avoid"],
        "Complete claim-support matrix. Internal phase wording in this frozen artifact is project provenance, not manuscript narrative.", "tab:claim-support", "p{1.8cm}p{4.0cm}p{2.0cm}p{4.5cm}p{4.5cm}p{4.5cm}",
    ))
    parts.append(r"\section{Reproducibility artifact table}")
    parts.append(longtable(
        manifest,
        ["phase", "path", "rows", "columns", "bytes", "sha256"],
        ["Bundle", "Path", "Rows", "Columns", "Bytes", "SHA256 (prefix/status)"],
        "Complete Phase 1/2 and DD-submission artifact index.", "tab:artifacts", "p{2.3cm}p{17.0cm}rrrr",
    ))
    parts.append(r"""\section{Reproduction commands}
The release root contains \texttt{environment.yml}, \texttt{requirements-lock.txt}, a container recipe, \texttt{REPRODUCIBILITY.md}, \texttt{DATA\_PROVENANCE.md} and \texttt{run\_all.sh}. The acceptance commands are:
\begin{verbatim}
pytest -q
python -m sourceaware.phase2.cli check --phase1 outputs/phase1_v2 --out outputs/phase2_v1
python scripts/generate_benchmark_card.py --check
python scripts/build_submission_figures.py --check
python scripts/audit_manuscript_claims.py --check
git diff --check
\end{verbatim}
Regeneration logs, test logs, benchmark-card checks and figure-build logs are archived with the release.
""")
    parts.append(r"\bibliography{references}\bibliographystyle{rsc}\end{document}")
    return "\n\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1", type=Path, default=DEFAULT_PHASE1)
    parser.add_argument("--phase2", type=Path, default=DEFAULT_PHASE2)
    parser.add_argument("--dd-out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manuscript-dir", type=Path, required=True)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tex = build_tex(args.phase1, args.phase2, args.dd_out, args.manuscript_dir)
    out = args.manuscript_dir / "supplementary_information.tex"
    out.write_text(tex)
    if args.compile:
        result = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", out.name],
            cwd=args.manuscript_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        (args.manuscript_dir / "supplementary_compile.log").write_text(result.stdout)
        if result.returncode:
            print(result.stdout[-8000:])
            raise SystemExit(result.returncode)
    if args.check:
        pdf = args.manuscript_dir / "supplementary_information.pdf"
        if not pdf.exists() or pdf.stat().st_size < 100_000:
            raise SystemExit("supplementary_information.pdf missing or too small")
        required = ["Full model inventory", "All label-view metrics", "All top-$K$ tables", "JARVIS portability", "Claim support matrix", "Reproducibility artifact table"]
        missing = [item for item in required if item not in tex]
        if missing:
            raise SystemExit(f"SI sections missing: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
