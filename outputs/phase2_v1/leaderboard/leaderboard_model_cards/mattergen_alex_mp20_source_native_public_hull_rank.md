# MatterGen_alex_mp20_source_native_public_hull_rank

Family: public_hull_oracle
Model role: baseline
Score status: scored
Coverage: 36802
Missing: 0
Source of score: MatterGen_alex_mp20_source_native_public_hull_rank
External WBM rows audited: 0
External score status: not_applicable
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 9.0
Label uncertainty band stable_yield@1000: 0.746
Top-K stable-yield band @1000: 0.254
Best label view stable_yield@1000: alexmp20_native
Worst label view stable_yield@1000: audit_view
Top-K uncertain burden audit_view@1000: 0.254

## Label-view metrics

| denominator           | model_name                                         | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:---------------------------------------------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.842473 |    0.842473 |   0.842473 |            0.866805 |   0.91752  |   0.867819 |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.814169 |    0.814169 |   0.814169 |            0.861133 |   0.91829  |   0.792808 |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.847628 |    0.847628 |   0.847628 |            0.842181 |   0.92033  |   0.934505 |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.284245 |    0.284245 |   0.284245 |            0.465394 |   0.57064  |   0.346193 |
| D5_full_complete      | MatterGen_alex_mp20_source_native_public_hull_rank | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.712238 |    0.712238 |   0.712238 |            0.806086 |   0.930265 |   0.713738 |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.842424 |    0.842424 |   0.842424 |            0.866797 |   0.917484 |   0.867703 |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.814143 |    0.814143 |   0.814143 |            0.861124 |   0.918274 |   0.792744 |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.847628 |    0.847628 |   0.847628 |            0.842187 |   0.920335 |   0.934504 |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.285058 |    0.285058 |   0.285058 |            0.465543 |   0.570275 |   0.346613 |
| D5_family_complete    | MatterGen_alex_mp20_source_native_public_hull_rank | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.711605 |    0.711605 |   0.711605 |            0.80572  |   0.930203 |   0.713308 |
| D5_max_coverage_union | MatterGen_alex_mp20_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.842424 |    0.842424 |   0.842424 |            0.866797 |   0.917484 |   0.867703 |
| D5_max_coverage_union | MatterGen_alex_mp20_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_max_coverage_union | MatterGen_alex_mp20_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.814143 |    0.814143 |   0.814143 |            0.861124 |   0.918274 |   0.792744 |
| D5_max_coverage_union | MatterGen_alex_mp20_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.847628 |    0.847628 |   0.847628 |            0.842187 |   0.920335 |   0.934504 |