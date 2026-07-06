# MP_common_pool_public_hull_rank

Family: public_hull_oracle
Coverage: 36770
Rank stability score: 4.0
Label uncertainty band stable_yield@1000: 0.507

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth.

## Label-view metrics

| denominator           | model_name                      | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:--------------------------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | MP_common_pool_public_hull_rank | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.772328 |    0.772328 |   0.772328 |            0.807495 |   0.869469 |   0.752056 |
| D5_full_complete      | MP_common_pool_public_hull_rank | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.6692   |    0.6692   |   0.6692   |            0.740955 |   0.825891 |   0.642143 |
| D5_full_complete      | MP_common_pool_public_hull_rank | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.583135 |    0.583135 |   0.583135 |            0.688486 |   0.793287 |   0.565633 |
| D5_full_complete      | MP_common_pool_public_hull_rank | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MP_common_pool_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | MP_common_pool_public_hull_rank | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MP_common_pool_public_hull_rank | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.467133 |    0.467133 |   0.467133 |            0.601995 |   0.686926 |   0.45936  |
| D5_full_complete      | MP_common_pool_public_hull_rank | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.501107 |    0.501107 |   0.501107 |            0.663811 |   0.847654 |   0.529429 |
| D5_family_complete    | MP_common_pool_public_hull_rank | mp_native       | 36770 |        0.408648 | stability             | ok                                                 |   0.772328 |    0.772328 |   0.772328 |            0.807499 |   0.869475 |   0.752056 |
| D5_family_complete    | MP_common_pool_public_hull_rank | alexmp20_native | 36770 |        0.36149  | stability             | ok                                                 |   0.6692   |    0.6692   |   0.6692   |            0.740959 |   0.825898 |   0.642143 |
| D5_family_complete    | MP_common_pool_public_hull_rank | alex_pbe_native | 36770 |        0.330895 | stability             | ok                                                 |   0.583135 |    0.583135 |   0.583135 |            0.68849  |   0.793295 |   0.565633 |
| D5_family_complete    | MP_common_pool_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MP_common_pool_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | MP_common_pool_public_hull_rank | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MP_common_pool_public_hull_rank | uncertain       | 36770 |        0.330568 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.467133 |    0.467133 |   0.467133 |            0.602    |   0.686939 |   0.45936  |
| D5_family_complete    | MP_common_pool_public_hull_rank | audit_view      | 36770 |        0.258009 | stability             | ok                                                 |   0.501107 |    0.501107 |   0.501107 |            0.663814 |   0.847659 |   0.529429 |
| D5_max_coverage_union | MP_common_pool_public_hull_rank | mp_native       | 36770 |        0.408648 | stability             | ok                                                 |   0.772328 |    0.772328 |   0.772328 |            0.807499 |   0.869475 |   0.752056 |
| D5_max_coverage_union | MP_common_pool_public_hull_rank | alexmp20_native | 36770 |        0.36149  | stability             | ok                                                 |   0.6692   |    0.6692   |   0.6692   |            0.740959 |   0.825898 |   0.642143 |
| D5_max_coverage_union | MP_common_pool_public_hull_rank | alex_pbe_native | 36770 |        0.330895 | stability             | ok                                                 |   0.583135 |    0.583135 |   0.583135 |            0.68849  |   0.793295 |   0.565633 |
| D5_max_coverage_union | MP_common_pool_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |