# MP_source_native_public_hull_rank

Family: public_hull_oracle
Coverage: 36802
Rank stability score: 7.0
Label uncertainty band stable_yield@1000: 0.696

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth.

## Label-view metrics

| denominator           | model_name                        | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:----------------------------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | MP_source_native_public_hull_rank | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MP_source_native_public_hull_rank | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.811315 |    0.811315 |   0.811315 |            0.852244 |   0.907246 |   0.785276 |
| D5_full_complete      | MP_source_native_public_hull_rank | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.72935  |    0.72935  |   0.72935  |            0.797749 |   0.879757 |   0.701578 |
| D5_full_complete      | MP_source_native_public_hull_rank | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.87917  |    0.87917  |   0.87917  |            0.874851 |   0.943987 |   0.956578 |
| D5_full_complete      | MP_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | MP_source_native_public_hull_rank | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_full_complete      | MP_source_native_public_hull_rank | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.358618 |    0.358618 |   0.358618 |            0.520944 |   0.61473  |   0.385992 |
| D5_full_complete      | MP_source_native_public_hull_rank | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.624223 |    0.624223 |   0.624223 |            0.746775 |   0.898486 |   0.631372 |
| D5_family_complete    | MP_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MP_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.811278 |    0.811278 |   0.811278 |            0.852239 |   0.907224 |   0.785215 |
| D5_family_complete    | MP_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.729386 |    0.729386 |   0.729386 |            0.797792 |   0.879776 |   0.701576 |
| D5_family_complete    | MP_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.87917  |    0.87917  |   0.87917  |            0.874855 |   0.943991 |   0.956578 |
| D5_family_complete    | MP_source_native_public_hull_rank | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | MP_source_native_public_hull_rank | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_family_complete    | MP_source_native_public_hull_rank | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.359317 |    0.359317 |   0.359317 |            0.521056 |   0.614213 |   0.386317 |
| D5_family_complete    | MP_source_native_public_hull_rank | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.623801 |    0.623801 |   0.623801 |            0.74657  |   0.898462 |   0.631036 |
| D5_max_coverage_union | MP_source_native_public_hull_rank | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   1        |    1        |   1        |            1        |   1        |   1        |
| D5_max_coverage_union | MP_source_native_public_hull_rank | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.811278 |    0.811278 |   0.811278 |            0.852239 |   0.907224 |   0.785215 |
| D5_max_coverage_union | MP_source_native_public_hull_rank | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.729386 |    0.729386 |   0.729386 |            0.797792 |   0.879776 |   0.701576 |
| D5_max_coverage_union | MP_source_native_public_hull_rank | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.87917  |    0.87917  |   0.87917  |            0.874855 |   0.943991 |   0.956578 |