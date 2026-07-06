# ALIGNN-FF

Family: strong_gnn
Model role: real_model
Score status: scored
Coverage: 36802
Missing: 0
Source of score: ALIGNN-FF_sourceaware_model_score
External WBM rows audited: 256963
External score status: downloaded_external_unmapped
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 5.0
Label uncertainty band stable_yield@1000: 0.254
Top-K stable-yield band @1000: 0.254
Best label view stable_yield@1000: common_pool
Worst label view stable_yield@1000: audit_view
Top-K uncertain burden audit_view@1000: 0.311

## Label-view metrics

| denominator           | model_name   | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | ALIGNN-FF    | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.350326 |    0.350326 |   0.350326 |            0.450677 |   0.463316 |   0.380142 |
| D5_full_complete      | ALIGNN-FF    | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.310864 |    0.310864 |   0.310864 |            0.460347 |   0.470727 |   0.335124 |
| D5_full_complete      | ALIGNN-FF    | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.291773 |    0.291773 |   0.291773 |            0.470758 |   0.482722 |   0.31276  |
| D5_full_complete      | ALIGNN-FF    | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.48338  |    0.48338  |   0.48338  |            0.464912 |   0.477647 |   0.496373 |
| D5_full_complete      | ALIGNN-FF    | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | ALIGNN-FF    | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.32982  |    0.32982  |   0.32982  |            0.454756 |   0.472533 |   0.360079 |
| D5_full_complete      | ALIGNN-FF    | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.308104 |    0.308104 |   0.308104 |            0.483214 |   0.477223 |   0.317312 |
| D5_full_complete      | ALIGNN-FF    | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.225466 |    0.225466 |   0.225466 |            0.478066 |   0.488453 |   0.245924 |
| D5_family_complete    | ALIGNN-FF    | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.350273 |    0.350273 |   0.350273 |            0.45077  |   0.463388 |   0.38004  |
| D5_family_complete    | ALIGNN-FF    | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.310902 |    0.310902 |   0.310902 |            0.460468 |   0.470788 |   0.33506  |
| D5_family_complete    | ALIGNN-FF    | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.291886 |    0.291886 |   0.291886 |            0.470884 |   0.482799 |   0.31275  |
| D5_family_complete    | ALIGNN-FF    | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.48338  |    0.48338  |   0.48338  |            0.46493  |   0.477681 |   0.496373 |
| D5_family_complete    | ALIGNN-FF    | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | ALIGNN-FF    | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   0.32982  |    0.32982  |   0.32982  |            0.45477  |   0.472567 |   0.360079 |
| D5_family_complete    | ALIGNN-FF    | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.308854 |    0.308854 |   0.308854 |            0.483332 |   0.477355 |   0.317979 |
| D5_family_complete    | ALIGNN-FF    | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.22515  |    0.22515  |   0.22515  |            0.478015 |   0.488453 |   0.245689 |
| D5_max_coverage_union | ALIGNN-FF    | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.350273 |    0.350273 |   0.350273 |            0.45077  |   0.463388 |   0.38004  |
| D5_max_coverage_union | ALIGNN-FF    | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.310902 |    0.310902 |   0.310902 |            0.460468 |   0.470788 |   0.33506  |
| D5_max_coverage_union | ALIGNN-FF    | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.291886 |    0.291886 |   0.291886 |            0.470884 |   0.482799 |   0.31275  |
| D5_max_coverage_union | ALIGNN-FF    | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.48338  |    0.48338  |   0.48338  |            0.46493  |   0.477681 |   0.496373 |