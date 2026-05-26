# Model-Facing Benchmark Sensitivity Check

This completed diagnostic uses one real model ranking, CHGNet, on a deterministic 5,000-structure subset of the 43,139 strict MP-Alex denominator. Scores are negative CHGNet formation-energy proxies constructed from CHGNet structure energies and MP elemental reference structures. The result is not a leaderboard and does not compare multiple models; it checks whether the label-source effect observed in the oracle/source-label analysis also appears under a real ranking.

The score-direction sanity check is intentionally reported before interpretation. The raw formation-energy proxy direction has AUROC above 0.5 on this subset, while the negative-formation direction used for the frozen ranking has AUROC below 0.5. This is not promoted as a model-quality result: raw CHGNet formation-energy proxies are not composition-aware hull-distance predictors, and this diagnostic is used only to measure label-source sensitivity under a real, reproducible ranking.

## Scoring Manifest

| model   |   n_scored |   n_target |   sample_seed |   batch_size | device   | mp_structure_cache                                                                                                                                     | mp_structure_cache_sha256                                        | claim_scope                                    |
|:--------|-----------:|-----------:|--------------:|-------------:|:---------|:-------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------|:-----------------------------------------------|
| CHGNet  |       5000 |       5000 |      20260523 |           64 | cuda     | /home/waas/paper_experiments/github/discordance-/outputs/milestones/materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl | fe9763ec3d931cdb6e3095fe36dcd2d47be4f2e50935a015d63c70855e6565ef | model_facing_sensitivity_check_not_leaderboard |

## Threshold-Free Metrics

| model   | denominator           | label_source   |    n |   positive_rate |    auroc |    auprc |   median_threshold_precision |   median_threshold_f1 | claim_scope                                    |   delta_vs_alex_auroc |   delta_vs_alex_auprc |
|:--------|:----------------------|:---------------|-----:|----------------:|---------:|---------:|-----------------------------:|----------------------:|:-----------------------------------------------|----------------------:|----------------------:|
| CHGNet  | full_sample_5000      | mp_stable      | 5000 |        0.3928   | 0.454422 | 0.353325 |                     0.3336   |              0.373656 | model_facing_sensitivity_check_not_leaderboard |            -0.0118587 |             0.0369094 |
| CHGNet  | full_sample_5000      | alex_stable    | 5000 |        0.3462   | 0.466281 | 0.316415 |                     0.3      |              0.354526 | model_facing_sensitivity_check_not_leaderboard |           nan         |           nan         |
| CHGNet  | source_agreement_only | mp_stable      | 4441 |        0.353074 | 0.456434 | 0.316525 |                     0.293111 |              0.343626 | model_facing_sensitivity_check_not_leaderboard |           nan         |           nan         |

## Score-Direction Sanity Check

| score_variant                                                    | label_source   |    n |   positive_rate |    auroc |    auprc | interpretation                                                                                                     | claim_scope                                    |
|:-----------------------------------------------------------------|:---------------|-----:|----------------:|---------:|---------:|:-------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------|
| raw_CHGNet_formation_energy_proxy_as_higher_stability_score      | mp_stable      | 5000 |          0.3928 | 0.545578 | 0.385406 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |
| raw_CHGNet_formation_energy_proxy_as_higher_stability_score      | alex_stable    | 5000 |          0.3462 | 0.533719 | 0.334352 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |
| negative_CHGNet_formation_energy_proxy_as_higher_stability_score | mp_stable      | 5000 |          0.3928 | 0.454422 | 0.353325 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |
| negative_CHGNet_formation_energy_proxy_as_higher_stability_score | alex_stable    | 5000 |          0.3462 | 0.466281 | 0.316415 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |
| random_ranking_baseline                                          | mp_stable      | 5000 |          0.3928 | 0.483138 | 0.379617 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |
| random_ranking_baseline                                          | alex_stable    | 5000 |          0.3462 | 0.481978 | 0.333788 | direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor | model_facing_sensitivity_check_not_leaderboard |

## Precision at K

| model   | denominator           | label_source     |    K |   precision_at_K |   stable_n_at_K |   discordant_fraction_at_K | claim_scope                                    |
|:--------|:----------------------|:-----------------|-----:|-----------------:|----------------:|---------------------------:|:-----------------------------------------------|
| CHGNet  | full_sample_5000      | mp_stable        |  100 |         0.37     |              37 |                      0.15  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | mp_stable        |  300 |         0.333333 |             100 |                      0.11  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | mp_stable        |  500 |         0.304    |             152 |                      0.084 | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | mp_stable        | 1000 |         0.261    |             261 |                      0.08  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | mp_stable        | 2000 |         0.292    |             584 |                      0.09  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | alex_stable      |  100 |         0.34     |              34 |                      0.15  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | alex_stable      |  300 |         0.29     |              87 |                      0.11  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | alex_stable      |  500 |         0.268    |             134 |                      0.084 | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | alex_stable      | 1000 |         0.237    |             237 |                      0.08  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | full_sample_5000      | alex_stable      | 2000 |         0.262    |             524 |                      0.09  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | source_agreement_only | agreement_stable |  100 |         0.37     |              37 |                      0     | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | source_agreement_only | agreement_stable |  300 |         0.276667 |              83 |                      0     | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | source_agreement_only | agreement_stable |  500 |         0.268    |             134 |                      0     | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | source_agreement_only | agreement_stable | 1000 |         0.222    |             222 |                      0     | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | source_agreement_only | agreement_stable | 2000 |         0.271    |             542 |                      0     | model_facing_sensitivity_check_not_leaderboard |

## MP-minus-Alex Precision Shift

|    K |   mp_precision_at_K |   alex_precision_at_K |   metric_shift_mp_minus_alex | model   | claim_scope                                    |
|-----:|--------------------:|----------------------:|-----------------------------:|:--------|:-----------------------------------------------|
|  100 |            0.37     |                 0.34  |                    0.03      | CHGNet  | model_facing_sensitivity_check_not_leaderboard |
|  300 |            0.333333 |                 0.29  |                    0.0433333 | CHGNet  | model_facing_sensitivity_check_not_leaderboard |
|  500 |            0.304    |                 0.268 |                    0.036     | CHGNet  | model_facing_sensitivity_check_not_leaderboard |
| 1000 |            0.261    |                 0.237 |                    0.024     | CHGNet  | model_facing_sensitivity_check_not_leaderboard |
| 2000 |            0.292    |                 0.262 |                    0.03      | CHGNet  | model_facing_sensitivity_check_not_leaderboard |

## Top-K Discordance Decomposition

| model   |    K |   both_stable_n |   mp_only_stable_n |   alex_only_stable_n |   both_unstable_n |   mp_stable_n |   alex_stable_n |   mp_minus_alex_stable_n |   source_discordant_n |   source_discordant_fraction | claim_scope                                    |
|:--------|-----:|----------------:|-------------------:|---------------------:|------------------:|--------------:|----------------:|-------------------------:|----------------------:|-----------------------------:|:-----------------------------------------------|
| CHGNet  |  100 |              28 |                  9 |                    6 |                57 |            37 |              34 |                        3 |                    15 |                        0.15  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  |  300 |              77 |                 23 |                   10 |               190 |           100 |              87 |                       13 |                    33 |                        0.11  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  |  500 |             122 |                 30 |                   12 |               336 |           152 |             134 |                       18 |                    42 |                        0.084 | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | 1000 |             209 |                 52 |                   28 |               711 |           261 |             237 |                       24 |                    80 |                        0.08  | model_facing_sensitivity_check_not_leaderboard |
| CHGNet  | 2000 |             464 |                120 |                   60 |              1356 |           584 |             524 |                       60 |                   180 |                        0.09  | model_facing_sensitivity_check_not_leaderboard |

## Precision-Shift Bootstrap

| model   |    K |   mp_stable_n |   alex_stable_n |   observed_mp_minus_alex_precision_shift |   bootstrap_ci_low |   bootstrap_ci_high |   n_bootstrap |   bootstrap_seed | claim_scope                                    |
|:--------|-----:|--------------:|----------------:|-----------------------------------------:|-------------------:|--------------------:|--------------:|-----------------:|:-----------------------------------------------|
| CHGNet  |  100 |            37 |              34 |                                0.03      |        -0.05       |              0.1    |          2000 |         20260524 | uncertainty_for_model_facing_sensitivity_check |
| CHGNet  |  300 |           100 |              87 |                                0.0433333 |         0.00666667 |              0.08   |          2000 |         20260524 | uncertainty_for_model_facing_sensitivity_check |
| CHGNet  |  500 |           152 |             134 |                                0.036     |         0.012      |              0.062  |          2000 |         20260524 | uncertainty_for_model_facing_sensitivity_check |
| CHGNet  | 1000 |           261 |             237 |                                0.024     |         0.006      |              0.041  |          2000 |         20260524 | uncertainty_for_model_facing_sensitivity_check |
| CHGNet  | 2000 |           584 |             524 |                                0.03      |         0.017      |              0.0435 |          2000 |         20260524 | uncertainty_for_model_facing_sensitivity_check |

## Sample Representativeness

| comparison         | stratum      |     n |   mp_stable_rate |   alex_stable_rate |   discordance_rate |   median_n_sites |   median_n_elements | claim_scope                     |
|:-------------------|:-------------|------:|-----------------:|-------------------:|-------------------:|-----------------:|--------------------:|:--------------------------------|
| full_denominator   | overall      | 43139 |        0.391108  |          0.340203  |          0.117295  |               10 |                   3 | sample_representativeness_audit |
| full_denominator   | n_elements=1 |   349 |        0.166189  |          0.169054  |          0.151862  |              nan |                   1 | sample_representativeness_audit |
| full_denominator   | n_elements=2 |  8707 |        0.396003  |          0.361663  |          0.125531  |              nan |                   2 | sample_representativeness_audit |
| full_denominator   | n_elements=3 | 24781 |        0.441709  |          0.381219  |          0.126992  |              nan |                   3 | sample_representativeness_audit |
| full_denominator   | n_elements=4 |  8090 |        0.279234  |          0.232138  |          0.0866502 |              nan |                   4 | sample_representativeness_audit |
| full_denominator   | n_elements=5 |  1147 |        0.135135  |          0.120314  |          0.0531822 |              nan |                   5 | sample_representativeness_audit |
| full_denominator   | n_elements=6 |    62 |        0.0967742 |          0.0645161 |          0.0645161 |              nan |                   6 | sample_representativeness_audit |
| full_denominator   | n_elements=7 |     3 |        0         |          0.333333  |          0.333333  |              nan |                   7 | sample_representativeness_audit |
| chgnet_5000_sample | overall      |  5000 |        0.3928    |          0.3462    |          0.1118    |              nan |                   3 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=1 |    33 |        0.181818  |          0.151515  |          0.0909091 |              nan |                   1 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=2 |  1013 |        0.39388   |          0.365252  |          0.121422  |              nan |                   2 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=3 |  2881 |        0.449844  |          0.390837  |          0.122874  |              nan |                   3 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=4 |   922 |        0.267896  |          0.232104  |          0.0770065 |              nan |                   4 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=5 |   145 |        0.103448  |          0.110345  |          0.0482759 |              nan |                   5 | sample_representativeness_audit |
| chgnet_5000_sample | n_elements=6 |     6 |        0.166667  |          0         |          0.166667  |              nan |                   6 | sample_representativeness_audit |
