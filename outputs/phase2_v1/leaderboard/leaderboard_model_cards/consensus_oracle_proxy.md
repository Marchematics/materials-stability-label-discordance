# consensus_oracle_proxy

Family: sourceaware_oracle
Model role: baseline
Score status: scored
Coverage: 36802
Missing: 0
Source of score: phase2_oracle_baseline
External WBM rows audited: 0
External score status: not_applicable
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 11.0
Label uncertainty band stable_yield@1000: 1.0
Top-K uncertain burden audit_view@1000: 0.0

## Label-view metrics

| denominator           | model_name             | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-----------------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | consensus_oracle_proxy | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.631372 |    0.631372 |   0.631372 |            0.688312 |   0.687452 |   0.778309 |
| D5_full_complete      | consensus_oracle_proxy | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.713738 |    0.713738 |   0.713738 |            0.775832 |   0.766067 |   0.820604 |
| D5_full_complete      | consensus_oracle_proxy | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.779732 |    0.779732 |   0.779732 |            0.835399 |   0.823213 |   0.85812  |
| D5_full_complete      | consensus_oracle_proxy | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.575458 |    0.575458 |   0.575458 |            0.560282 |   0.579085 |   0.769494 |
| D5_full_complete      | consensus_oracle_proxy | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | consensus_oracle_proxy | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | consensus_oracle_proxy | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0        |    0        |   0        |            0.253088 |   0        |   0.187297 |
| D5_full_complete      | consensus_oracle_proxy | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | consensus_oracle_proxy | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.631036 |    0.631036 |   0.631036 |            0.688106 |   0.687285 |   0.778068 |
| D5_family_complete    | consensus_oracle_proxy | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.713308 |    0.713308 |   0.713308 |            0.775533 |   0.76574  |   0.820296 |
| D5_family_complete    | consensus_oracle_proxy | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.779156 |    0.779156 |   0.779156 |            0.834981 |   0.822781 |   0.857731 |
| D5_family_complete    | consensus_oracle_proxy | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.575458 |    0.575458 |   0.575458 |            0.560297 |   0.579085 |   0.769488 |
| D5_family_complete    | consensus_oracle_proxy | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | consensus_oracle_proxy | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | consensus_oracle_proxy | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0        |    0        |   0        |            0.252448 |   0        |   0.187668 |
| D5_family_complete    | consensus_oracle_proxy | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_max_coverage_union | consensus_oracle_proxy | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.631036 |    0.631036 |   0.631036 |            0.688106 |   0.687285 |   0.778068 |
| D5_max_coverage_union | consensus_oracle_proxy | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.713308 |    0.713308 |   0.713308 |            0.775533 |   0.76574  |   0.820296 |
| D5_max_coverage_union | consensus_oracle_proxy | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.779156 |    0.779156 |   0.779156 |            0.834981 |   0.822781 |   0.857731 |
| D5_max_coverage_union | consensus_oracle_proxy | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.575458 |    0.575458 |   0.575458 |            0.560297 |   0.579085 |   0.769488 |