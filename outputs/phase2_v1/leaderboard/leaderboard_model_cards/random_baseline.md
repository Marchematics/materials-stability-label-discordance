# random_baseline

Family: random_baseline
Model role: baseline
Score status: scored
Coverage: 36802
Missing: 0
Source of score: phase2_deterministic_baseline
External WBM rows audited: 0
External score status: not_applicable
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 6.0
Label uncertainty band stable_yield@1000: 0.24
Top-K uncertain burden audit_view@1000: 0.313

## Label-view metrics

| denominator           | model_name      | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:----------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | random_baseline | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.407893 |    0.407893 |   0.407893 |            0.499352 |   0.497949 |   0.406338 |
| D5_full_complete      | random_baseline | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.359239 |    0.359239 |   0.359239 |            0.498229 |   0.499115 |   0.360659 |
| D5_full_complete      | random_baseline | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.328347 |    0.328347 |   0.328347 |            0.49809  |   0.496432 |   0.328666 |
| D5_full_complete      | random_baseline | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.515468 |    0.515468 |   0.515468 |            0.498147 |   0.49645  |   0.513394 |
| D5_full_complete      | random_baseline | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | random_baseline | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.384948 |    0.384948 |   0.384948 |            0.499607 |   0.498222 |   0.38406  |
| D5_full_complete      | random_baseline | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.329659 |    0.329659 |   0.329659 |            0.499314 |   0.499024 |   0.328309 |
| D5_full_complete      | random_baseline | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.258775 |    0.258775 |   0.258775 |            0.500511 |   0.498964 |   0.258059 |
| D5_family_complete    | random_baseline | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.407676 |    0.407676 |   0.407676 |            0.499295 |   0.497885 |   0.406139 |
| D5_family_complete    | random_baseline | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.359098 |    0.359098 |   0.359098 |            0.498203 |   0.499024 |   0.360491 |
| D5_family_complete    | random_baseline | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.328269 |    0.328269 |   0.328269 |            0.49807  |   0.49642  |   0.328588 |
| D5_family_complete    | random_baseline | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.515468 |    0.515468 |   0.515468 |            0.498164 |   0.496481 |   0.513393 |
| D5_family_complete    | random_baseline | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | random_baseline | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   0.384948 |    0.384948 |   0.384948 |            0.49962  |   0.498253 |   0.384059 |
| D5_family_complete    | random_baseline | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.330024 |    0.330024 |   0.330024 |            0.499158 |   0.498864 |   0.328815 |
| D5_family_complete    | random_baseline | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.258564 |    0.258564 |   0.258564 |            0.500525 |   0.499062 |   0.257865 |
| D5_max_coverage_union | random_baseline | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.407676 |    0.407676 |   0.407676 |            0.499295 |   0.497885 |   0.406139 |
| D5_max_coverage_union | random_baseline | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.359098 |    0.359098 |   0.359098 |            0.498203 |   0.499024 |   0.360491 |
| D5_max_coverage_union | random_baseline | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.328269 |    0.328269 |   0.328269 |            0.49807  |   0.49642  |   0.328588 |
| D5_max_coverage_union | random_baseline | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.515468 |    0.515468 |   0.515468 |            0.498164 |   0.496481 |   0.513393 |