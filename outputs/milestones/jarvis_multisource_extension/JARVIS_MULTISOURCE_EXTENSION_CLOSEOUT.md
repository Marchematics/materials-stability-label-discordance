# JARVIS multi-source extension closeout

This milestone adds JARVIS-DFT as a third public source while preserving the MP--alex-mp-20 audit as the primary result.

## Scope

- JARVIS source: JARVIS OPTIMADE `jarvisdft` records queried on 2026-07-04, with `dft_3d_` identifiers, structure fields and `_jarvis_ehull`.
- Matching rule: reduced-formula prefilter followed by `pymatgen` `StructureMatcher` exact matching with the same default settings as the MP--alex-mp-20 audit (`ltol=0.2`, `stol=0.3`, `angle_tol=5`, `primitive_cell=True`, `scale=True`, `attempt_supercell=True`).
- No formula-only match is used as a result.
- No common hull is reconstructed.
- Primary MP--alex-mp-20 result remains the 43,139-row strict denominator.

## Outcome

The primary triple denominator contains 23300 single-JARVIS exact matched MP--alex-mp-20 rows, so the JARVIS extension is interpreted as a **triple exact-match source-conflict result**.

## Output tables

- `table_multisource_denominator_flow.csv`
- `table_jarvis_download_scope.csv`
- `table_jarvis_default_exact_matches.csv`
- `table_jarvis_structure_matching_tolerance_sweep.csv`
- `table_jarvis_multiple_match_tie_break_sensitivity.csv`
- `table_pairwise_source_conflict_rates.csv`
- `table_three_source_label_composition.csv`
- `figure5_panel_a_denominator_flow.csv`
- `figure5_panel_b_pairwise_conflicts.csv`
- `figure5_panel_c_label_composition.csv`

## Denominator flow

```csv
step,n,scope
archived_MP_alex_mp20_strict_denominator,43139,primary_MP_alex_mp20_result
jarvis_optimade_cached_records,79637,raw_cache_not_public_output
jarvis_dft_3d_records_with_structure_and_ehull,75993,candidate_third_source_pool
denominator_rows_with_formula_candidate_in_jarvis,31270,prefilter_only_not_match_result
jarvis_default_exact_structure_match_rows,36544,third_source_exact_match_rows
jarvis_unique_matched_denominator_rows,28273,third_source_exact_match_denominator
jarvis_single_match_denominator_rows,23300,primary_triple_denominator_for_rates
jarvis_multiple_match_denominator_rows,4973,duplicate_match_boundary
```

