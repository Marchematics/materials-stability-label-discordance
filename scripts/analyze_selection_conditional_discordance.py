from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
MATCHES = OUT / "table_route_b_full_snapshot_matches.csv"
SCORES = OUT / "table_route_b_full_snapshot_model_scores.csv"


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
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT)}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_joined() -> pd.DataFrame:
    matches = pd.read_csv(MATCHES)
    matches = matches[matches["match_status"].eq("strict_structure_match")].copy()
    matches["discordant"] = matches["mp_stable_exact"].astype(bool) != matches["alex_stable_exact"].astype(bool)
    scores = pd.read_csv(SCORES)
    scores = scores[scores["score_status"].eq("scored")].copy()
    scores["score"] = pd.to_numeric(scores["score"], errors="coerce")
    return scores.merge(
        matches[["material_id", "mp_stable_exact", "alex_stable_exact", "discordant"]],
        on="material_id",
        how="inner",
    )


def bin_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    bins = [
        ("top_10", 0.00, 0.10),
        ("top_10_25", 0.10, 0.25),
        ("top_25_50", 0.25, 0.50),
        ("bottom_50", 0.50, 1.00),
    ]
    rows = []
    top_rows = []
    for model, mdf in df.groupby("model"):
        ordered = mdf.sort_values("score", ascending=True).reset_index(drop=True)
        n = len(ordered)
        baseline = float(ordered["discordant"].mean())
        top_n = max(math.ceil(0.10 * n), 20)
        for label, lo, hi in bins:
            start = int(math.floor(lo * n))
            end = int(math.ceil(hi * n))
            if label == "top_10":
                start, end = 0, top_n
            chunk = ordered.iloc[start:end].copy()
            disc = float(chunk["discordant"].mean()) if len(chunk) else math.nan
            rows.append(
                {
                    "model": model,
                    "bin": label,
                    "rank_start_inclusive": start + 1,
                    "rank_end_inclusive": end,
                    "n_bin": len(chunk),
                    "discordant_n": int(chunk["discordant"].sum()),
                    "discordance_rate": disc,
                    "baseline_discordance": baseline,
                    "enrichment_vs_baseline": disc / baseline if baseline > 0 else math.nan,
                    "score_min": float(chunk["score"].min()) if len(chunk) else math.nan,
                    "score_max": float(chunk["score"].max()) if len(chunk) else math.nan,
                }
            )
        top = ordered.iloc[:top_n].copy()
        top_rows.append(
            {
                "model": model,
                "n_common": n,
                "top_n": top_n,
                "baseline_discordance": baseline,
                "top_decile_discordance": float(top["discordant"].mean()),
                "top_decile_discordant_n": int(top["discordant"].sum()),
                "top_decile_enrichment": float(top["discordant"].mean()) / baseline if baseline > 0 else math.nan,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(top_rows)


def permutation_test(df: pd.DataFrame, n_perm: int = 2000, seed: int = 20260520) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for model, mdf in df.groupby("model"):
        ordered = mdf.sort_values("score", ascending=True).reset_index(drop=True)
        labels = ordered["discordant"].astype(int).to_numpy()
        n = len(labels)
        top_n = max(math.ceil(0.10 * n), 20)
        baseline = float(labels.mean())
        observed_top = float(labels[:top_n].mean())
        observed_enrichment = observed_top / baseline if baseline > 0 else math.nan
        perm_top = np.empty(n_perm)
        for i in range(n_perm):
            shuffled = rng.permutation(labels)
            perm_top[i] = shuffled[:top_n].mean()
        p_ge = float((np.sum(perm_top >= observed_top) + 1) / (n_perm + 1))
        rows.append(
            {
                "model": model,
                "n_common": n,
                "top_n": top_n,
                "baseline_discordance": baseline,
                "observed_top_decile_discordance": observed_top,
                "observed_enrichment": observed_enrichment,
                "permutation_n": n_perm,
                "permutation_p_ge_observed": p_ge,
                "permutation_mean_top_decile_discordance": float(perm_top.mean()),
                "permutation_p95_top_decile_discordance": float(np.quantile(perm_top, 0.95)),
            }
        )
    return pd.DataFrame(rows)


def go_no_go(top: pd.DataFrame, perm: pd.DataFrame) -> pd.DataFrame:
    merged = top.merge(perm[["model", "permutation_p_ge_observed"]], on="model", how="left")
    pass_models = merged[
        (merged["top_decile_discordance"] >= 0.30)
        & (merged["top_decile_enrichment"] >= 2.0)
        & (merged["permutation_p_ge_observed"] <= 0.10)
    ]
    return pd.DataFrame(
        [
            {
                "hypothesis": "selection_conditional_discordance",
                "n_models": len(merged),
                "models_tested": "|".join(merged["model"].tolist()),
                "models_passing_top_decile_gate": "|".join(pass_models["model"].tolist()),
                "n_models_passing": len(pass_models),
                "launch_gate": "PASS" if len(pass_models) >= 2 else "NO_GO",
                "gate_definition": "at_least_two_models_with_top_decile_discordance_ge_0.30_enrichment_ge_2_and_permutation_p_le_0.10",
                "claim_scope": "minimal_MP_Alex_route_B_denominator_selection_conditional_diagnostic",
            }
        ]
    )


def write_closeout(go: pd.DataFrame, top: pd.DataFrame) -> None:
    row = go.iloc[0]
    text = f"""# Selection-Conditional Discordance Diagnostic

## Question

Does MP-vs-alex label discordance concentrate in the candidates that ML models
rank as most stable?

## Input

```text
denominator: Route B MP-vs-alex strict-structure matches
n_common: {int(top['n_common'].iloc[0]) if not top.empty else 'NA'}
models: {' | '.join(top['model'].tolist())}
score direction: lower score = more stable
```

## Gate

The NMI launch gate for this refined hypothesis requires at least two models to
show:

```text
top-decile discordance >= 0.30
enrichment over full-denominator baseline >= 2.0
permutation p <= 0.10
```

## Result

```text
launch_gate: {row['launch_gate']}
models_passing: {row['models_passing_top_decile_gate']}
```

This result is a diagnostic of the refined selection-conditional hypothesis. It
does not alter the Route B full-snapshot no-go result unless the gate passes.
"""
    (OUT / "SELECTION_CONDITIONAL_DISCORDANCE_CLOSEOUT.md").write_text(text, encoding="utf-8")


def main() -> None:
    joined = load_joined()
    binned, top = bin_rows(joined)
    perm = permutation_test(joined)
    go = go_no_go(top, perm)
    binned.to_csv(OUT / "table_selection_conditional_discordance_by_bin.csv", index=False)
    top.to_csv(OUT / "table_selection_conditional_top_decile_summary.csv", index=False)
    perm.to_csv(OUT / "table_selection_conditional_permutation.csv", index=False)
    go.to_csv(OUT / "table_selection_conditional_go_no_go.csv", index=False)
    write_closeout(go, top)
    write_manifest()


if __name__ == "__main__":
    main()
