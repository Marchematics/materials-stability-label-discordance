# MACE-MP

Family: universal_potential
Model role: real_model
Score status: scored
Coverage: 36802
Missing: 0
Source of score: MACE-MP_sourceaware_model_score
External WBM rows audited: 0
External score status: figshare_download_unavailable_http_403
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 6.0
Label uncertainty band stable_yield@1000: 0.2879999999999999
Top-K stable-yield band @1000: 0.2879999999999999
Best label view stable_yield@1000: common_pool
Worst label view stable_yield@1000: audit_view
Top-K uncertain burden audit_view@1000: 0.354

## Label-view metrics

| denominator           | model_name   | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | MACE-MP      | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.379609 |    0.379609 |   0.379609 |            0.475436 |   0.487103 |   0.40522  |
| D5_full_complete      | MACE-MP      | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.342612 |    0.342612 |   0.342612 |            0.485209 |   0.496415 |   0.359267 |
| D5_full_complete      | MACE-MP      | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.315279 |    0.315279 |   0.315279 |            0.488324 |   0.499    |   0.328586 |
| D5_full_complete      | MACE-MP      | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.497513 |    0.497513 |   0.497513 |            0.479551 |   0.495517 |   0.518296 |
| D5_full_complete      | MACE-MP      | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | MACE-MP      | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.36218  |    0.36218  |   0.36218  |            0.481083 |   0.497565 |   0.38637  |
| D5_full_complete      | MACE-MP      | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.315508 |    0.315508 |   0.315508 |            0.488745 |   0.483215 |   0.323716 |
| D5_full_complete      | MACE-MP      | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.25477  |    0.25477  |   0.25477  |            0.497812 |   0.506091 |   0.261354 |
| D5_family_complete    | MACE-MP      | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.379407 |    0.379407 |   0.379407 |            0.475398 |   0.487187 |   0.405154 |
| D5_family_complete    | MACE-MP      | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.342632 |    0.342632 |   0.342632 |            0.48531  |   0.496475 |   0.359228 |
| D5_family_complete    | MACE-MP      | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.31521  |    0.31521  |   0.31521  |            0.488313 |   0.499054 |   0.328588 |
| D5_family_complete    | MACE-MP      | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.497513 |    0.497513 |   0.497513 |            0.479568 |   0.49555  |   0.518296 |
| D5_family_complete    | MACE-MP      | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | MACE-MP      | consensus       | 24615 |        0.385415 | stability             | ok                                                 |   0.36218  |    0.36218  |   0.36218  |            0.481097 |   0.497598 |   0.38637  |
| D5_family_complete    | MACE-MP      | uncertain       | 36802 |        0.33115  | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.316485 |    0.316485 |   0.316485 |            0.489037 |   0.4832   |   0.324248 |
| D5_family_complete    | MACE-MP      | audit_view      | 36802 |        0.257785 | stability             | ok                                                 |   0.254664 |    0.254664 |   0.254664 |            0.497898 |   0.506142 |   0.261152 |
| D5_max_coverage_union | MACE-MP      | mp_native       | 36802 |        0.40851  | stability             | ok                                                 |   0.379407 |    0.379407 |   0.379407 |            0.475398 |   0.487187 |   0.405154 |
| D5_max_coverage_union | MACE-MP      | alexmp20_native | 36802 |        0.361393 | stability             | ok                                                 |   0.342632 |    0.342632 |   0.342632 |            0.48531  |   0.496475 |   0.359228 |
| D5_max_coverage_union | MACE-MP      | alex_pbe_native | 36802 |        0.330852 | stability             | ok                                                 |   0.31521  |    0.31521  |   0.31521  |            0.488313 |   0.499054 |   0.328588 |
| D5_max_coverage_union | MACE-MP      | common_pool     | 31873 |        0.51724  | stability             | ok                                                 |   0.497513 |    0.497513 |   0.497513 |            0.479568 |   0.49555  |   0.518296 |