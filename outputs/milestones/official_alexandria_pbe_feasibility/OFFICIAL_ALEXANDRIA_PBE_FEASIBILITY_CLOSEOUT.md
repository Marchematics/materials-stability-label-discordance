# Official Alexandria-PBE feasibility closeout

Scope: feasibility audit only. This is a source-native public-label portability check, not a common-hull reconstruction and not a mechanism attribution.

- Alexandria source: complete PBE 3D JSON snapshot `2025.07.02`.
- Retrieval date: `2026-07-05`.
- Stability field found in complete JSON: `entries[].data.e_above_hull` in eV/atom.
- Matching rule: reduced-formula prefilter followed by pymatgen `StructureMatcher` exact-structure matching.
- MP identifiers are used only as MP row identifiers; official Alexandria rows are not joined by MP-ID.

## Denominator flow

| step                                                            |       n | scope                                                     |
|:----------------------------------------------------------------|--------:|:----------------------------------------------------------|
| official_alexandria_pbe_complete_3d_shards_downloaded           |      58 | complete_PBE_3D_json_not_convex_hull_only                 |
| official_alexandria_pbe_complete_3d_records_parsed              | 5777914 | complete_PBE_3D_json_not_convex_hull_only                 |
| official_alexandria_records_with_e_above_hull_formula_structure |  187015 | after_MP_alex_mp20_formula_prefilter                      |
| primary_MP_alex_mp20_strict_denominator_rows                    |   43139 | existing_primary_denominator                              |
| denominator_rows_with_official_alexandria_formula_candidate     |   42818 | formula_prefilter_only_not_structure_match                |
| official_alexandria_exact_structure_match_rows                  |   48755 | StructureMatcher_formula_prefilter_result                 |
| official_alexandria_unique_matched_denominator_rows             |   41760 | MP_alex_mp20_official_Alexandria_triple_overlap           |
| official_alexandria_single_match_denominator_rows               |   36802 | primary_single_match_triple_denominator_if_used_for_rates |
| official_alexandria_multiple_match_denominator_rows             |    4958 | duplicate_match_boundary_requires_sensitivity_if_claimed  |

## Feasibility decision

`main_text_candidate`

Decision thresholds used: >20,000 unique MP--official Alexandria matches supports main-text consideration; 5,000--10,000 single-match triple rows supports a main table/figure or extended-data result; smaller or ambiguous coverage remains a Supplementary coverage boundary.
