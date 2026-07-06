# prevalence_dummy

Family: dummy_baseline
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

Rank stability score: 5.0
Label uncertainty band stable_yield@1000: 0.194
Top-K stable-yield band @1000: 0.14100000000000001
Best label view stable_yield@1000: mp_native
Worst label view stable_yield@1000: audit_view
Top-K uncertain burden audit_view@1000: 0.257

## Label-view metrics

| denominator           | model_name       | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |   auroc |      auprc |
|:----------------------|:-----------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|--------:|-----------:|
| D5_full_complete      | prevalence_dummy | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.372754 |    0.372754 |   0.372754 |            0.469641 |     0.5 |   0.408659 |
| D5_full_complete      | prevalence_dummy | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.349985 |    0.349985 |   0.349985 |            0.490983 |     0.5 |   0.3615   |
| D5_full_complete      | prevalence_dummy | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.338374 |    0.338374 |   0.338374 |            0.505583 |     0.5 |   0.330904 |
| D5_full_complete      | prevalence_dummy | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.444377 |    0.444377 |   0.444377 |            0.424515 |     0.5 |   0.517257 |
| D5_full_complete      | prevalence_dummy | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        |   nan   | nan        |
| D5_full_complete      | prevalence_dummy | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.347844 |    0.347844 |   0.347844 |            0.46942  |     0.5 |   0.385431 |
| D5_full_complete      | prevalence_dummy | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.33731  |    0.33731  |   0.33731  |            0.505028 |     0.5 |   0.330577 |
| D5_full_complete      | prevalence_dummy | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.228629 |    0.228629 |   0.228629 |            0.480197 |     0.5 |   0.258016 |
| D5_family_complete    | prevalence_dummy | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.372622 |    0.372622 |   0.372622 |            0.469663 |     0.5 |   0.40851  |
| D5_family_complete    | prevalence_dummy | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.34985  |    0.34985  |   0.34985  |            0.490962 |     0.5 |   0.361393 |
| D5_family_complete    | prevalence_dummy | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.338288 |    0.338288 |   0.338288 |            0.505557 |     0.5 |   0.330852 |
| D5_family_complete    | prevalence_dummy | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.444316 |    0.444316 |   0.444316 |            0.424472 |     0.5 |   0.51724  |
| D5_family_complete    | prevalence_dummy | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        |   nan   | nan        |
| D5_family_complete    | prevalence_dummy | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   0.347844 |    0.347844 |   0.347844 |            0.469434 |     0.5 |   0.385415 |
| D5_family_complete    | prevalence_dummy | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.338147 |    0.338147 |   0.338147 |            0.50523  |     0.5 |   0.33115  |
| D5_family_complete    | prevalence_dummy | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.228102 |    0.228102 |   0.228102 |            0.480004 |     0.5 |   0.257785 |
| D5_max_coverage_union | prevalence_dummy | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.372622 |    0.372622 |   0.372622 |            0.469663 |     0.5 |   0.40851  |
| D5_max_coverage_union | prevalence_dummy | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.34985  |    0.34985  |   0.34985  |            0.490962 |     0.5 |   0.361393 |
| D5_max_coverage_union | prevalence_dummy | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.338288 |    0.338288 |   0.338288 |            0.505557 |     0.5 |   0.330852 |
| D5_max_coverage_union | prevalence_dummy | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.444316 |    0.444316 |   0.444316 |            0.424472 |     0.5 |   0.51724  |