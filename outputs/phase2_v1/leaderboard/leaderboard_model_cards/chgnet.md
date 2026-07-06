# CHGNet

Family: universal_potential
Model role: real_model
Score status: scored
Coverage: 36801
Missing: 1
Source of score: CHGNet_sourceaware_model_score
External WBM rows audited: 0
External score status: figshare_download_unavailable_http_403
Included in primary leaderboard: True

Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.

## Leaderboard alpha summary

Rank stability score: 7.0
Label uncertainty band stable_yield@1000: 0.279
Top-K uncertain burden audit_view@1000: 0.354

## Label-view metrics

| denominator           | model_name   | label_view      |     n |   positive_rate | label_semantics       | metric_status                                      |         f1 |   precision |     recall |   balanced_accuracy |      auroc |      auprc |
|:----------------------|:-------------|:----------------|------:|----------------:|:----------------------|:---------------------------------------------------|-----------:|------------:|-----------:|--------------------:|-----------:|-----------:|
| D5_full_complete      | CHGNet       | mp_native       | 36769 |        0.408659 | stability             | ok                                                 |   0.361374 |    0.361374 |   0.361374 |            0.460018 |   0.466342 |   0.386132 |
| D5_full_complete      | CHGNet       | alexmp20_native | 36769 |        0.3615   | stability             | ok                                                 |   0.318011 |    0.318011 |   0.318011 |            0.465944 |   0.476458 |   0.342428 |
| D5_full_complete      | CHGNet       | alex_pbe_native | 36769 |        0.330904 | stability             | ok                                                 |   0.288978 |    0.288978 |   0.288978 |            0.46867  |   0.481244 |   0.314781 |
| D5_full_complete      | CHGNet       | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.484593 |    0.484593 |   0.484593 |            0.466169 |   0.477148 |   0.501159 |
| D5_full_complete      | CHGNet       | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_full_complete      | CHGNet       | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.338463 |    0.338463 |   0.338463 |            0.461788 |   0.473161 |   0.365256 |
| D5_full_complete      | CHGNet       | uncertain       | 36769 |        0.330577 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.309338 |    0.309338 |   0.309338 |            0.484136 |   0.479227 |   0.321301 |
| D5_full_complete      | CHGNet       | audit_view      | 36769 |        0.258016 | stability             | ok                                                 |   0.223464 |    0.223464 |   0.223464 |            0.476716 |   0.487983 |   0.247988 |
| D5_family_complete    | CHGNet       | mp_native       | 36801 |        0.408522 | stability             | ok                                                 |   0.361115 |    0.361115 |   0.361115 |            0.459925 |   0.466379 |   0.386028 |
| D5_family_complete    | CHGNet       | alexmp20_native | 36801 |        0.361403 | stability             | ok                                                 |   0.31782  |    0.31782  |   0.31782  |            0.465875 |   0.476496 |   0.34237  |
| D5_family_complete    | CHGNet       | alex_pbe_native | 36801 |        0.330861 | stability             | ok                                                 |   0.289011 |    0.289011 |   0.289011 |            0.468729 |   0.481287 |   0.314767 |
| D5_family_complete    | CHGNet       | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.484593 |    0.484593 |   0.484593 |            0.466169 |   0.477148 |   0.501159 |
| D5_family_complete    | CHGNet       | source_union    |     0 |      nan        | stability             | not_evaluable_full_source_union_incomplete         | nan        |  nan        | nan        |          nan        | nan        | nan        |
| D5_family_complete    | CHGNet       | consensus       | 24614 |        0.385431 | stability             | ok                                                 |   0.338463 |    0.338463 |   0.338463 |            0.461788 |   0.473161 |   0.365256 |
| D5_family_complete    | CHGNet       | uncertain       | 36801 |        0.331159 | uncertainty_indicator | uncertainty_indicator_not_primary_stability_metric |   0.310577 |    0.310577 |   0.310577 |            0.484613 |   0.479302 |   0.321952 |
| D5_family_complete    | CHGNet       | audit_view      | 36801 |        0.257792 | stability             | ok                                                 |   0.223253 |    0.223253 |   0.223253 |            0.476732 |   0.487977 |   0.247756 |
| D5_max_coverage_union | CHGNet       | mp_native       | 36801 |        0.408522 | stability             | ok                                                 |   0.361115 |    0.361115 |   0.361115 |            0.459925 |   0.466379 |   0.386028 |
| D5_max_coverage_union | CHGNet       | alexmp20_native | 36801 |        0.361403 | stability             | ok                                                 |   0.31782  |    0.31782  |   0.31782  |            0.465875 |   0.476496 |   0.34237  |
| D5_max_coverage_union | CHGNet       | alex_pbe_native | 36801 |        0.330861 | stability             | ok                                                 |   0.289011 |    0.289011 |   0.289011 |            0.468729 |   0.481287 |   0.314767 |
| D5_max_coverage_union | CHGNet       | common_pool     | 31872 |        0.517257 | stability             | ok                                                 |   0.484593 |    0.484593 |   0.484593 |            0.466169 |   0.477148 |   0.501159 |