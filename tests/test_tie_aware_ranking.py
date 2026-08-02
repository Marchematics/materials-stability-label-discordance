import numpy as np

from sourceaware.ranking import analytic_tie_aware_topk, score_tie_audit


def test_analytic_tie_expectation_and_bounds() -> None:
    scores = [3.0, 2.0, 2.0, 2.0, 1.0]
    labels = [1, 1, 0, 0, 1]
    result = analytic_tie_aware_topk(scores, labels, 3)
    assert result["strictly_before_boundary_n"] == 1
    assert result["boundary_tie_n"] == 3
    assert result["selected_from_boundary_n"] == 2
    assert result["expected_stable_hits"] == 1 + 2 / 3
    assert result["best_worst_low_hits"] == 1
    assert result["best_worst_high_hits"] == 2


def test_tie_aware_statistics_are_permutation_invariant() -> None:
    scores = np.array([3.0, 2.0, 2.0, 2.0, 1.0])
    labels = np.array([1, 1, 0, 0, 1])
    expected = analytic_tie_aware_topk(scores, labels, 3)
    permutation = np.array([4, 2, 0, 3, 1])
    observed = analytic_tie_aware_topk(scores[permutation], labels[permutation], 3)
    assert observed == expected


def test_tie_audit_reports_boundary_occupancy() -> None:
    audit = score_tie_audit([0.0, 0.0, 0.0, -1.0], [2])
    row = audit.iloc[0]
    assert row["maximum_score_tie_block_n"] == 3
    assert row["strictly_before_boundary_n"] == 0
    assert row["boundary_tie_n"] == 3
    assert row["selected_from_boundary_n"] == 2
