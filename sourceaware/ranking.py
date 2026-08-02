"""Ranking utilities with explicit, analytic treatment of score ties."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import hypergeom


DEFAULT_TIE_DECIMALS = 12


def tie_key(scores: Iterable[float], decimals: int = DEFAULT_TIE_DECIMALS) -> np.ndarray:
    """Return the predeclared numerical equivalence key used for score ties."""
    values = np.asarray(scores, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Tie keys require finite scores")
    return np.round(values, decimals=decimals)


def analytic_tie_aware_topk(
    scores: Iterable[float],
    labels: Iterable[bool | int],
    k: int,
    *,
    tie_decimals: int = DEFAULT_TIE_DECIMALS,
    interval: float = 0.95,
) -> dict[str, float | int]:
    """Calculate exact top-K expectation and tie-only uncertainty.

    Scores are ranked from high to low. If K intersects a tied boundary block,
    selection within that block is treated as uniform without replacement. The
    number of positives drawn from the boundary block is therefore exactly
    hypergeometric; no Monte Carlo tie randomisation is used.
    """
    score = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    if score.ndim != 1 or y.ndim != 1 or len(score) != len(y):
        raise ValueError("scores and labels must be one-dimensional and equally sized")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("labels must be binary")
    if not 1 <= int(k) <= len(score):
        raise ValueError("k must lie between 1 and the number of rows")
    if not 0 < interval < 1:
        raise ValueError("interval must lie in (0, 1)")

    key = tie_key(score, tie_decimals)
    boundary = np.sort(key)[::-1][int(k) - 1]
    before = key > boundary
    block = key == boundary
    a = int(before.sum())
    b = int(block.sum())
    r = int(k) - a
    h = int(y[before].sum())
    s = int(y[block].sum())

    expected = float(h + r * s / b)
    lower_tail = (1.0 - interval) / 2.0
    x_low = int(hypergeom.ppf(lower_tail, M=b, n=s, N=r))
    x_high = int(hypergeom.ppf(1.0 - lower_tail, M=b, n=s, N=r))
    minimum = int(h + max(0, r - (b - s)))
    maximum = int(h + min(r, s))

    return {
        "K": int(k),
        "boundary_score": float(boundary),
        "strictly_before_boundary_n": a,
        "strictly_before_boundary_positive_n": h,
        "boundary_tie_n": b,
        "boundary_tie_positive_n": s,
        "selected_from_boundary_n": r,
        "expected_stable_hits": expected,
        "expected_stable_yield": expected / int(k),
        "tie_interval_low_hits": int(h + x_low),
        "tie_interval_high_hits": int(h + x_high),
        "tie_interval_low_yield": float((h + x_low) / int(k)),
        "tie_interval_high_yield": float((h + x_high) / int(k)),
        "best_worst_low_hits": minimum,
        "best_worst_high_hits": maximum,
        "best_worst_low_yield": float(minimum / int(k)),
        "best_worst_high_yield": float(maximum / int(k)),
        "tie_interval_level": float(interval),
        "tie_decimals": int(tie_decimals),
    }


def score_tie_audit(
    scores: Iterable[float],
    k_values: Iterable[int],
    *,
    tie_decimals: int = DEFAULT_TIE_DECIMALS,
) -> pd.DataFrame:
    """Describe global and K-boundary tie occupancy without using row order."""
    score = np.asarray(scores, dtype=float)
    key = tie_key(score, tie_decimals)
    counts = pd.Series(key).value_counts()
    rows = []
    for k in k_values:
        if not 1 <= int(k) <= len(score):
            continue
        boundary = np.sort(key)[::-1][int(k) - 1]
        rows.append(
            {
                "K": int(k),
                "row_n": int(len(score)),
                "unique_score_n": int(len(counts)),
                "rows_in_non_singleton_ties_n": int(counts[counts > 1].sum()),
                "largest_tie_block_n": int(counts.max()),
                "maximum_score_tie_block_n": int(counts.loc[key.max()]),
                "boundary_score": float(boundary),
                "strictly_before_boundary_n": int((key > boundary).sum()),
                "boundary_tie_n": int((key == boundary).sum()),
                "selected_from_boundary_n": int(k - (key > boundary).sum()),
                "tie_decimals": int(tie_decimals),
            }
        )
    return pd.DataFrame(rows)
