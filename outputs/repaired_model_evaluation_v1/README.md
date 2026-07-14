# Repaired model-evaluation analysis

This directory contains the primary model-facing analysis. Raw predicted
energies per atom are retained for provenance and construct-validity auditing.

## Fixed-support estimand

The label-only comparison uses the M1 31,872-row common-support cohort shared by MP-native,
MatterGen alex-mp-20-native, official Alexandria-PBE-native, matched
common-pool and audit labels. Each model uses the same predicted-hull ranking
and the same row set for every one of these views. The consensus label is a
selection policy: it retains 24,614 agreement rows and is reported separately,
rather than being included in the label-only band.

`all_view_common_support_exclusion_audit.csv` records the route from D2 to M1:
D2 has 36,802 rows; D5 has 36,801 archived four-score rows; five label views
are evaluable for 31,873 rows; their intersection is M1. Thus 4,929 D5 rows
are excluded because at least one label-only view is not evaluable, and the
one label-supported row absent from M1 has no CHGNet score.

## Model score construction

`scripts/build_predicted_hull_scores.py` converts stored raw model energies to
predicted formation energies using model-specific elemental references. It then
computes predicted energy above hull on the fixed D2 subsystem phase pool.
`score_for_stability_ranking` is the negative of that predicted hull distance.
`fixed_subsystem_phase_pool_manifest.json` records the pool construction and
input checksums.

## Uncertainty

`evaluate_repaired_model_comparison.py` uses a paired chemical-system cluster
bootstrap (1,000 replicates; seed 20260714). All label views are resampled
together within each replicate. The released tables report label-view bands,
paired label-view differences with 95% quantile intervals and directional
probabilities, and the probability that each model is the metric winner.
