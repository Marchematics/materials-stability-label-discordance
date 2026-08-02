# Figure and claim lock

**Status:** `figure_and_claim_lock_complete`

Ranking, matching, denominator, and claim-source decisions were locked before manuscript rewriting. The post-write zero-context paper-to-evidence audit passed with no unresolved claim mismatch.

## K-dependent model-decision audit (0 meV physical coordinates)

|    K | endpoint                         | point winner(s)                    | winner frequency                                           |   first-second margin (hits) |   MP-selection regret median (hits) |   MP-selection regret 95% upper (hits) |   boundary tie max |
|-----:|:---------------------------------|:-----------------------------------|:-----------------------------------------------------------|-----------------------------:|------------------------------------:|---------------------------------------:|-------------------:|
|  100 | alex_pbe_matched_pool_coordinate | ALIGNN-FF, CHGNet, M3GNet, MACE-MP | ALIGNN-FF=1.000, CHGNet=1.000, M3GNet=1.000, MACE-MP=1.000 |                        0.000 |                               0.000 |                                  0.000 |                  1 |
|  100 | alex_pbe_source_coordinate       | M3GNet                             | M3GNet=0.679                                               |                        2.000 |                               1.000 |                                  7.000 |                  1 |
|  100 | alexmp20_source_coordinate       | ALIGNN-FF, M3GNet, MACE-MP         | ALIGNN-FF=0.353, M3GNet=0.421, MACE-MP=0.400               |                        0.000 |                               1.000 |                                  6.000 |                  1 |
|  100 | mp_matched_pool_coordinate       | ALIGNN-FF, CHGNet, M3GNet, MACE-MP | ALIGNN-FF=1.000, CHGNet=1.000, M3GNet=1.000, MACE-MP=1.000 |                        0.000 |                               0.000 |                                  0.000 |                  1 |
|  100 | mp_source_coordinate             | M3GNet, MACE-MP                    | M3GNet=0.548, MACE-MP=0.353                                |                        0.000 |                               0.000 |                                  0.000 |                  1 |
|  300 | alex_pbe_matched_pool_coordinate | ALIGNN-FF, CHGNet, M3GNet, MACE-MP | ALIGNN-FF=1.000, CHGNet=1.000, M3GNet=1.000, MACE-MP=1.000 |                        0.000 |                               0.000 |                                  0.000 |                  1 |
|  300 | alex_pbe_source_coordinate       | M3GNet                             | M3GNet=0.903                                               |                        8.000 |                               0.000 |                                  9.000 |                  1 |
|  300 | alexmp20_source_coordinate       | M3GNet                             | M3GNet=0.864                                               |                        8.000 |                               0.000 |                                  8.000 |                  1 |
|  300 | mp_matched_pool_coordinate       | M3GNet                             | M3GNet=0.383                                               |                        1.000 |                               0.000 |                                  3.000 |                  1 |
|  300 | mp_source_coordinate             | M3GNet                             | M3GNet=0.783                                               |                        7.000 |                               0.000 |                                  0.000 |                  1 |
|  500 | alex_pbe_matched_pool_coordinate | CHGNet, M3GNet, MACE-MP            | CHGNet=1.000, M3GNet=1.000, MACE-MP=1.000                  |                        0.000 |                               0.000 |                                  2.000 |                  1 |
|  500 | alex_pbe_source_coordinate       | M3GNet                             | M3GNet=0.608                                               |                        1.000 |                               0.000 |                                 12.000 |                  1 |
|  500 | alexmp20_source_coordinate       | MACE-MP                            | MACE-MP=0.368                                              |                        1.000 |                               0.000 |                                  9.000 |                  1 |
|  500 | mp_matched_pool_coordinate       | M3GNet, MACE-MP                    | M3GNet=0.766, MACE-MP=0.904                                |                        0.000 |                               0.000 |                                  6.025 |                  1 |
|  500 | mp_source_coordinate             | MACE-MP                            | MACE-MP=0.433                                              |                        1.000 |                               0.000 |                                  0.000 |                  1 |
| 1000 | alex_pbe_matched_pool_coordinate | CHGNet                             | CHGNet=0.933                                               |                        1.000 |                               3.000 |                                  7.000 |                  1 |
| 1000 | alex_pbe_source_coordinate       | M3GNet                             | M3GNet=0.764                                               |                        7.000 |                               1.000 |                                 17.000 |                  1 |
| 1000 | alexmp20_source_coordinate       | M3GNet                             | M3GNet=0.857                                               |                       10.000 |                               3.000 |                                 18.000 |                  1 |
| 1000 | mp_matched_pool_coordinate       | M3GNet                             | M3GNet=0.723                                               |                        3.000 |                               1.000 |                                  7.000 |                  1 |
| 1000 | mp_source_coordinate             | MACE-MP                            | MACE-MP=0.777                                              |                        5.000 |                               0.000 |                                  0.000 |                  1 |
| 5000 | alex_pbe_matched_pool_coordinate | MACE-MP                            | MACE-MP=0.993                                              |                       19.000 |                               0.000 |                                  0.000 |                  1 |
| 5000 | alex_pbe_source_coordinate       | MACE-MP                            | MACE-MP=1.000                                              |                      118.000 |                               0.000 |                                  0.000 |                  1 |
| 5000 | alexmp20_source_coordinate       | MACE-MP                            | MACE-MP=1.000                                              |                      129.000 |                               0.000 |                                  0.000 |                  1 |
| 5000 | mp_matched_pool_coordinate       | MACE-MP                            | MACE-MP=0.831                                              |                       12.000 |                               0.000 |                                 13.000 |                  1 |
| 5000 | mp_source_coordinate             | MACE-MP                            | MACE-MP=1.000                                              |                       85.000 |                               0.000 |                                  0.000 |                  1 |

## Matching sensitivity

| matching_tolerance   |   d1_retained_n |   d2_retained_n |   mphys_tolerance_specific_n |   equivalence_class_n |   non_singleton_equivalence_class_n |   largest_equivalence_class_n |   default_ranking_max_abs_difference_vs_primary |
|:---------------------|----------------:|----------------:|-----------------------------:|----------------------:|------------------------------------:|------------------------------:|------------------------------------------------:|
| tight                |           42799 |           35877 |                        35745 |                 35746 |                                 918 |                             6 |                                             nan |
| default              |           43139 |           36802 |                        36650 |                 35740 |                                 922 |                             6 |                                               0 |
| loose                |           43139 |           36802 |                        36650 |                 35449 |                                1155 |                             6 |                                             nan |

Cross-source counts are survival counts on the frozen D1/D2 mappings; they do not search for new loose-tolerance matches. Rankings were independently recomputed with each tolerance-specific equivalence graph.

### Zero-threshold D2 switch burden

| matching_tolerance   | endpoint_a                 | endpoint_b                 |     n |   switch_n |   switch_rate |
|:---------------------|:---------------------------|:---------------------------|------:|-----------:|--------------:|
| tight                | mp_source_coordinate       | alexmp20_source_coordinate | 35877 |       4155 |        0.1158 |
| tight                | mp_source_coordinate       | alex_pbe_source_coordinate | 35877 |       5534 |        0.1542 |
| tight                | alexmp20_source_coordinate | alex_pbe_source_coordinate | 35877 |       3729 |        0.1039 |
| default              | mp_source_coordinate       | alexmp20_source_coordinate | 36802 |       4244 |        0.1153 |
| default              | mp_source_coordinate       | alex_pbe_source_coordinate | 36802 |       5666 |        0.1540 |
| default              | alexmp20_source_coordinate | alex_pbe_source_coordinate | 36802 |       3862 |        0.1049 |
| loose                | mp_source_coordinate       | alexmp20_source_coordinate | 36802 |       4244 |        0.1153 |
| loose                | mp_source_coordinate       | alex_pbe_source_coordinate | 36802 |       5666 |        0.1540 |
| loose                | alexmp20_source_coordinate | alex_pbe_source_coordinate | 36802 |       3862 |        0.1049 |

### Top-1000 decision check

| matching_tolerance   | coordinate_endpoint              | point_winner_models_json   |   first_second_margin_hits |   mp_selection_regret_max_hits |   maximum_boundary_tie_n_across_models |
|:---------------------|:---------------------------------|:---------------------------|---------------------------:|-------------------------------:|---------------------------------------:|
| tight                | alex_pbe_matched_pool_coordinate | ["CHGNet", "M3GNet"]       |                          0 |                              3 |                                      1 |
| tight                | alex_pbe_source_coordinate       | ["M3GNet"]                 |                          5 |                              5 |                                      1 |
| tight                | alexmp20_source_coordinate       | ["M3GNet"]                 |                          9 |                              9 |                                      1 |
| tight                | mp_matched_pool_coordinate       | ["M3GNet"]                 |                          1 |                              1 |                                      1 |
| tight                | mp_source_coordinate             | ["MACE-MP"]                |                          6 |                              0 |                                      1 |
| default              | alex_pbe_matched_pool_coordinate | ["CHGNet"]                 |                          1 |                              4 |                                      1 |
| default              | alex_pbe_source_coordinate       | ["M3GNet"]                 |                          7 |                              7 |                                      1 |
| default              | alexmp20_source_coordinate       | ["M3GNet"]                 |                         10 |                             10 |                                      1 |
| default              | mp_matched_pool_coordinate       | ["M3GNet"]                 |                          3 |                              3 |                                      1 |
| default              | mp_source_coordinate             | ["MACE-MP"]                |                          5 |                              0 |                                      1 |
| loose                | alex_pbe_matched_pool_coordinate | ["M3GNet"]                 |                          2 |                              0 |                                      1 |
| loose                | alex_pbe_source_coordinate       | ["M3GNet"]                 |                          8 |                              0 |                                      1 |
| loose                | alexmp20_source_coordinate       | ["M3GNet"]                 |                         11 |                              0 |                                      1 |
| loose                | mp_matched_pool_coordinate       | ["M3GNet"]                 |                          5 |                              0 |                                      1 |
| loose                | mp_source_coordinate             | ["M3GNet"]                 |                          1 |                              0 |                                      1 |

## Common-pool count lock

- All native MP--Alexandria-PBE conflicts: **5,666**.
- Reconstructable native conflicts: **5,661**.
- Unreconstructable native conflicts: **5**.
- Phase-pool-sensitive: **3,659**.
- Persistent: **2,002**.
- Hidden common-pool: **2,895**.
- Common-pool conflicts: **4,897**.

## Claim-source lock

- Machine-readable claims: **45**.
- Unique source files: **11**.
- Every claim ID is unique and every source path resolves.
- Abstract regret wording is locked as **1--3 stable hits per 1000 across the four non-MP endpoints**, or **0--3 across all five endpoints including the MP anchor**.

## Interpretation lock

- Full-ranking AUROC/AP/nAP selection remains stable: MACE-MP wins all five 0-meV physical endpoints in all 1,000 cluster-bootstrap replicates.
- Top-K point ordering is budget-, endpoint-, and matching-tolerance-specific among closely performing models.
- Model-selection consequences are reported with point winners, bootstrap winner frequencies, first--second margins, and regret in stable hits.
- The previous self-included predicted-hull discovery curves and row-ID-derived binary metrics remain withdrawn.
