# Benchmark Impact of Label-Source Choice

This completed milestone quantifies benchmark consequences of MP-vs-Alexandria label-source choice on the full 43,139 strict-match denominator. It deliberately does not claim a full-denominator ML model leaderboard, because full-denominator model scores are not available in the public-safe artifact set. Instead, it reports source-label transfer limits and source-native ranking references that any downstream benchmark must confront.

## Label Confusion

| label_cell              |     n |   fraction | claim_scope                                    |
|:------------------------|------:|-----------:|:-----------------------------------------------|
| both_stable             | 13244 |  0.307008  | completed_full_denominator_label_source_impact |
| mp_stable_alex_unstable |  3628 |  0.0841002 | completed_full_denominator_label_source_impact |
| mp_unstable_alex_stable |  1432 |  0.033195  | completed_full_denominator_label_source_impact |
| both_unstable           | 24835 |  0.575697  | completed_full_denominator_label_source_impact |

## Perfect Source-Labeler Cross-Evaluation

| predictor                         | evaluation_label_source        |     n |    tp |   fp |   fn |    tn |   precision |   recall |       f1 |   accuracy |   balanced_accuracy | claim_scope                                    |   delta_from_source_native_f1 |
|:----------------------------------|:-------------------------------|------:|------:|-----:|-----:|------:|------------:|---------:|---------:|-----------:|--------------------:|:-----------------------------------------------|------------------------------:|
| perfect_MP_source_labeler         | MP_source_native_truth         | 43139 | 16872 |    0 |    0 | 26267 |    1        | 1        | 1        |   1        |            1        | source_label_transfer_upper_bound_not_ml_model |                      0        |
| perfect_MP_source_labeler         | Alexandria_source_native_truth | 43139 | 13244 | 3628 | 1432 | 24835 |    0.784969 | 0.902426 | 0.839609 |   0.882705 |            0.887481 | source_label_transfer_upper_bound_not_ml_model |                     -0.160391 |
| perfect_Alexandria_source_labeler | MP_source_native_truth         | 43139 | 13244 | 1432 | 3628 | 24835 |    0.902426 | 0.784969 | 0.839609 |   0.882705 |            0.865226 | source_label_transfer_upper_bound_not_ml_model |                     -0.160391 |
| perfect_Alexandria_source_labeler | Alexandria_source_native_truth | 43139 | 14676 |    0 |    0 | 28463 |    1        | 1        | 1        |   1        |            1        | source_label_transfer_upper_bound_not_ml_model |                      0        |

## Source-Native Ranking Reference

| ranking                             |     K |   mp_stable_rate_at_K |   alex_stable_rate_at_K |   absolute_stable_rate_shift |   discordance_at_K | claim_scope                                         |
|:------------------------------------|------:|----------------------:|------------------------:|-----------------------------:|-------------------:|:----------------------------------------------------|
| MP_source_native_ehull_rank         |   100 |                1      |                0.84     |                     0.16     |           0.16     | source_native_oracle_ranking_reference_not_ml_model |
| MP_source_native_ehull_rank         |   300 |                1      |                0.826667 |                     0.173333 |           0.173333 | source_native_oracle_ranking_reference_not_ml_model |
| MP_source_native_ehull_rank         |   500 |                1      |                0.85     |                     0.15     |           0.15     | source_native_oracle_ranking_reference_not_ml_model |
| MP_source_native_ehull_rank         |  1000 |                1      |                0.844    |                     0.156    |           0.156    | source_native_oracle_ranking_reference_not_ml_model |
| MP_source_native_ehull_rank         |  5000 |                1      |                0.783    |                     0.217    |           0.217    | source_native_oracle_ranking_reference_not_ml_model |
| MP_source_native_ehull_rank         | 10000 |                1      |                0.7855   |                     0.2145   |           0.2145   | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank |   100 |                0.9    |                1        |                     0.1      |           0.1      | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank |   300 |                0.92   |                1        |                     0.08     |           0.08     | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank |   500 |                0.922  |                1        |                     0.078    |           0.078    | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank |  1000 |                0.922  |                1        |                     0.078    |           0.078    | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank |  5000 |                0.9088 |                1        |                     0.0912   |           0.0912   | source_native_oracle_ranking_reference_not_ml_model |
| Alexandria_source_native_ehull_rank | 10000 |                0.9043 |                1        |                     0.0957   |           0.0957   | source_native_oracle_ranking_reference_not_ml_model |

## Conflict-Excluded Denominator

| denominator                             |     n |   mp_stable_rate |   alex_stable_rate |   source_conflict_n |   source_conflict_fraction | claim_scope                                        |
|:----------------------------------------|------:|-----------------:|-------------------:|--------------------:|---------------------------:|:---------------------------------------------------|
| full_strict_MP_Alex                     | 43139 |         0.391108 |           0.340203 |                5060 |                   0.117295 | completed_full_denominator_label_source_impact     |
| source_agreement_only_conflict_excluded | 38079 |         0.347803 |           0.347803 |                   0 |                   0        | completed_conflict_excluded_denominator_definition |
| source_conflict_only                    |  5060 |         0.716996 |           0.283004 |                5060 |                   1        | completed_source_conflict_burden_definition        |

## Paper-Facing Interpretation

| impact_statement                            |     value | unit                                | paper_use                                                                       |
|:--------------------------------------------|----------:|:------------------------------------|:--------------------------------------------------------------------------------|
| binary_label_disagreement_burden            | 0.117295  | fraction_of_full_strict_denominator | completed benchmark-label source uncertainty number                             |
| MP_stable_candidates_rejected_by_Alexandria | 0.215031  | fraction_of_MP_stable_set           | upper-bound transfer loss for MP-native stable releases evaluated by Alexandria |
| Alexandria_stable_candidates_rejected_by_MP | 0.0975743 | fraction_of_Alexandria_stable_set   | upper-bound transfer loss for Alexandria-native stable releases evaluated by MP |
| conflict_excluded_denominator_retention     | 0.882705  | fraction_of_full_strict_denominator | cost of source-agreement-only benchmark reporting                               |
