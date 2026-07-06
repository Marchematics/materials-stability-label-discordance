# M3GNet

Family: universal_potential
Coverage: 36802
Rank stability score: 4.0
Label uncertainty band stable_yield@1000: 0.274

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth.

## Label-view metrics

| denominator           | model_name   | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | M3GNet       | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.373885 |    0.373885 |   0.373885 |            0.470597 |   0.480622 |   0.398398 |
| D5_full_complete      | M3GNet       | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.335992 |    0.335992 |   0.335992 |            0.480025 |   0.489476 |   0.352115 |
| D5_full_complete      | M3GNet       | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.306074 |    0.306074 |   0.306074 |            0.481445 |   0.492583 |   0.323346 |
| D5_full_complete      | M3GNet       | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.49078  |    0.49078  |   0.49078  |            0.472577 |   0.486208 |   0.510184 |
| D5_full_complete      | M3GNet       | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | M3GNet       | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.354274 |    0.354274 |   0.354274 |            0.474652 |   0.486897 |   0.377406 |
| D5_full_complete      | M3GNet       | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.312382 |    0.312382 |   0.312382 |            0.486409 |   0.481664 |   0.322612 |
| D5_full_complete      | M3GNet       | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.240434 |    0.240434 |   0.240434 |            0.488152 |   0.49808  |   0.255693 |
| D5_family_complete    | M3GNet       | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.373753 |    0.373753 |   0.373753 |            0.470619 |   0.48069  |   0.398286 |
| D5_family_complete    | M3GNet       | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.335789 |    0.335789 |   0.335789 |            0.479953 |   0.489523 |   0.35204  |
| D5_family_complete    | M3GNet       | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.306094 |    0.306094 |   0.306094 |            0.481501 |   0.492621 |   0.323313 |
| D5_family_complete    | M3GNet       | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.49078  |    0.49078  |   0.49078  |            0.472595 |   0.486241 |   0.510184 |
| D5_family_complete    | M3GNet       | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | M3GNet       | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   0.354274 |    0.354274 |   0.354274 |            0.474665 |   0.486931 |   0.377406 |
| D5_family_complete    | M3GNet       | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.313367 |    0.313367 |   0.313367 |            0.486706 |   0.481714 |   0.323228 |
| D5_family_complete    | M3GNet       | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.240434 |    0.240434 |   0.240434 |            0.488312 |   0.49811  |   0.255464 |
| D5_max_coverage_union | M3GNet       | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.373753 |    0.373753 |   0.373753 |            0.470619 |   0.48069  |   0.398286 |
| D5_max_coverage_union | M3GNet       | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.335789 |    0.335789 |   0.335789 |            0.479953 |   0.489523 |   0.35204  |
| D5_max_coverage_union | M3GNet       | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.306094 |    0.306094 |   0.306094 |            0.481501 |   0.492621 |   0.323313 |
| D5_max_coverage_union | M3GNet       | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.49078  |    0.49078  |   0.49078  |            0.472595 |   0.486241 |   0.510184 |