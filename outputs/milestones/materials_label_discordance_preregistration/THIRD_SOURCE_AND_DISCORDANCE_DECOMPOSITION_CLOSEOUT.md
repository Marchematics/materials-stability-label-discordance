# Third-Source and Discordance-Decomposition Diagnostics

## Scope

This milestone extends the MP-vs-Alex full-snapshot diagnostic with two checks:

1. a third-source OQMD exact-structure attempt; and
2. decomposition of MP-vs-Alex discordance by hull proximity, chemistry family
   and prototype proxy.

No new DFT, training or model fitting is used. OQMD rows are never promoted to a
three-source conclusion unless exact-structure coverage reaches the predeclared
`n_common >= 200` scale.

## Third-Source Result

```csv
comparison,n_common,discordance_rate,claim_scope
MP_vs_Alex,287,0.10801393728222997,completed_pairwise_baseline
MP_vs_OQMD,4,0.0,blocked_or_undercovered_third_source
Alex_vs_OQMD,4,0.0,blocked_or_undercovered_third_source
```

If the OQMD common denominator is undercovered, the paper role is a data-access
or source-coverage boundary, not a completed third-source measurement.

## Near-Hull Decomposition

```csv
band,n,discordant_n,discordance_rate
both_near_hull_25meV,181,22,0.12154696132596685
either_near_hull_25meV,213,31,0.14553990610328638
neither_near_hull_25meV,74,0,0.0
mp_near_hull_25meV,198,29,0.14646464646464646
alex_near_hull_25meV,196,24,0.12244897959183673
```

This is the main completed decomposition result: MP-vs-Alex discordance is
higher near the hull than away from the hull. It refines the conclusion from a
single baseline discordance number into a localized label-boundary phenomenon.

## Case-Analysis Contrast

```csv
case,n_common,discordance_rate,role
WBM_vs_alex_existing_probe,270,0.5222222222222223,case_analysis_high_discordance_source_selection_specific
MP_vs_alex_route_b_full_snapshot,287,0.10801393728222997,full_snapshot_pairwise_baseline
MP_vs_alex_top_decile_ALIGNN-FF,29,0.1724137931034483,selection_conditional_no_go_core_result
MP_vs_alex_top_decile_CHGNet,29,0.1034482758620689,selection_conditional_no_go_core_result
MP_vs_alex_top_decile_MACE-MP,29,0.1034482758620689,selection_conditional_no_go_core_result
```

The earlier WBM-vs-alex/PARC-style high-discordance probe is retained as a case
analysis. It is not used as the full-snapshot baseline.
