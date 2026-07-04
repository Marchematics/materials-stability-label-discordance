# Benchmark Reliability Enhancement

This milestone adds completed full-denominator reporting enhancements and freezes gated protocols for mechanism, third-source and benchmark-impact extensions. It does not downgrade the 43,139 strict-match result and does not add a new model benchmark.

## Completed from existing full denominator

- Strict MP-Alex matches: 43,139
- Discordant exact-stability labels: 5,060
- Full-denominator discordance: 0.1173
- MP-exact-stable selected subset discordance: 0.2150 (n=16,872)
- Alex-exact-stable selected subset discordance: 0.0976 (n=14,676)

Completed tables:

- `table_selection_conditioned_discordance_atlas.csv`
- `table_full_denominator_uncertainty_threshold_sweep.csv`
- `table_materials_case_atlas.csv`
- `table_source_aware_benchmark_card.csv`

## Frozen but not completed

- `table_common_hull_mechanism_protocol.csv` defines the common-hull/common-competitor mechanism decomposition gate.
- `table_third_source_expansion_protocol.csv` defines formula-query plus strict StructureMatcher third-source expansion gates.
- `table_benchmark_impact_protocol.csv` defines the full-denominator model-prediction gate for benchmark-impact claims.

Claim boundary: these gated protocols cannot be cited as completed mechanism, triangulation or full-denominator model-ranking evidence until their required inputs and outputs exist.
