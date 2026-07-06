# official_Alexandria_PBE_source_native_public_hull_rank

Family: public_hull_oracle
Model role: baseline
Score status: scored
Coverage: 36802
Missing: 0
Source of score: official_Alexandria_PBE_source_native_public_hull_rank
External WBM rows audited: 0
External score status: not_applicable
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 10.0
Label uncertainty band stable_yield@1000: 0.813
Top-K uncertain burden audit_view@1000: 0.187

## Label-view metrics

| denominator           | model_name                                             | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-------------------------------------------------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.813124 |    0.813124 |   0.813124 |            0.841989 |   0.902338 |   0.841209 |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.855251 |    0.855251 |   0.855251 |            0.886649 |   0.936128 |   0.861143 |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.838651 |    0.838651 |   0.838651 |            0.832883 |   0.914358 |   0.937513 |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.220485 |    0.220485 |   0.220485 |            0.417771 |   0.544514 |   0.324931 |
| D5_full_complete      | official_Alexandria_PBE_source_native_public_hull_rank | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.782861 |    0.782861 |   0.782861 |            0.853677 |   0.950883 |   0.779732 |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.813157 |    0.813157 |   0.813157 |            0.842057 |   0.902304 |   0.841051 |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.855188 |    0.855188 |   0.855188 |            0.886619 |   0.936046 |   0.860963 |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.838651 |    0.838651 |   0.838651 |            0.832889 |   0.914363 |   0.937513 |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.221548 |    0.221548 |   0.221548 |            0.418066 |   0.544173 |   0.325385 |
| D5_family_complete    | official_Alexandria_PBE_source_native_public_hull_rank | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.782228 |    0.782228 |   0.782228 |            0.853296 |   0.950778 |   0.779156 |
| D5_max_coverage_union | official_Alexandria_PBE_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.813157 |    0.813157 |   0.813157 |            0.842057 |   0.902304 |   0.841051 |
| D5_max_coverage_union | official_Alexandria_PBE_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.855188 |    0.855188 |   0.855188 |            0.886619 |   0.936046 |   0.860963 |
| D5_max_coverage_union | official_Alexandria_PBE_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_max_coverage_union | official_Alexandria_PBE_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.838651 |    0.838651 |   0.838651 |            0.832889 |   0.914363 |   0.937513 |