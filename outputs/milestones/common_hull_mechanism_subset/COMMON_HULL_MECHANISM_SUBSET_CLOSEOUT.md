# Common-Composition Hull Mechanism Subset

This milestone converts the prior common-hull protocol into a completed, deterministic subset analysis. It is intentionally labelled as a common-composition competitor-hull proxy because third-source/exact competitor structure matching and unclipped source energies are not yet complete.

The completed subset is a coverage-boundary result, not a positive mechanism-decomposition result. Under the public source-native tables available here, only a small fraction of sampled MP-Alex matched targets has a common-composition competitor set with both MP and Alexandria proxy formation energies. The result therefore supports the claim that full mechanism attribution requires a dedicated common-hull reconstruction or additional unclipped source-energy exports, rather than a lightweight table join.

| sample_role                 |    n |   common_available_n |   median_common_formula_count |   native_discordant_n |   common_available_fraction |
|:----------------------------|-----:|---------------------:|------------------------------:|----------------------:|----------------------------:|
| concordant_control_sample   |  500 |                    6 |                             1 |                     0 |                       0.012 |
| discordant_mechanism_sample | 1000 |                   10 |                             1 |                  1000 |                       0.01  |

| sample_role                 | mechanism_class                                |   n |   fraction_within_sample_role |
|:----------------------------|:-----------------------------------------------|----:|------------------------------:|
| concordant_control_sample   | common_hull_unavailable                        | 494 |                         0.988 |
| concordant_control_sample   | concordant_under_native_and_common_composition |   6 |                         0.012 |
| discordant_mechanism_sample | common_hull_unavailable                        | 990 |                         0.99  |
| discordant_mechanism_sample | energy_or_correction_driven_common_composition |  10 |                         0.01  |
