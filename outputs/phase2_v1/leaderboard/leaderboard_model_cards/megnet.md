# MEGNet

Family: early_gnn
Model role: external_target_not_scored
Score status: not_scored_no_exact_sourceaware_mapping_or_download
Coverage: 0
Missing: 36802
Source of score: matbench_discovery_public_wbm_prediction_downloaded_unmapped
External WBM rows audited: 256963
External score status: downloaded_external_unmapped
Included in primary leaderboard: False

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Not evaluated in SourceAware label-view leaderboard because exact SourceAware row scores are unavailable or the row is an external target audit.

## External WBM-native context

This section is contextual only: WBM IDs are not exact SourceAware row IDs, so these values are not SourceAware label-view metrics.

WBM-native AUPRC rank: 1
WBM-native AUROC rank: 2
WBM-native stable_yield@1000 rank: 1
WBM-native AUPRC: 0.228311392999976
WBM-native AUROC: 0.6508783259653005
WBM-native stable_yield@1000: 0.339
Context guardrail: Separate WBM-native context leaderboard; WBM IDs are not exact SourceAware row IDs and this table is not SourceAware rank evidence.

## Label-view metrics

No SourceAware label-view metrics for this inventory row.

## Failure / exclusion reason

Matbench/WBM predictions require WBM-to-SourceAware exact mapping or local score generation; recorded as ecosystem target, not primary SourceAware evidence.