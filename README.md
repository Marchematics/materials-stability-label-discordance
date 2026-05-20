# Materials Stability Label Discordance

Public-safe go/no-go artifact package for a prospective materials-label
discordance study.

This repository does **not** claim a completed NMI-ready paper result. It
freezes the first decision gates:

- data-access smoke check for Materials Project;
- exact-structure WBM/Matbench vs alex-mp binary-stability discordance probe;
- same-denominator model-conclusion checks using stable-class F1 as the
  primary ranking metric;
- explicit no-go boundaries for overclaiming.

## Current Outcome

The minimal exact-structure probe is strong:

```text
matched structures: 270
binary exact-stability discordance: 0.522
launch-signal gate: pass for this existing WBM-vs-alex probe
```

The downstream primary endpoint does **not** yet pass:

```text
primary models: ALIGNN-FF / CHGNet / MACE-MP
primary metric: stable-class F1
primary ranking flip: false
max absolute F1 delta: 0.022665
go/no-go: NO_GO_primary_no_material_F1_ranking_flip
```

Discovery-count consequences are present but supporting only:

```text
ALIGNN-FF stable-count: 5 -> 1
CHGNet stable-count: 16 -> 6
MACE-MP stable-count: 15 -> 6
```

## Route B One-Shot Rescue

The only permitted rescue is a single MP-vs-Alex full-snapshot attempt:

```text
Materials Project API-derived public records
vs independently downloaded Alexandria/alex-mp snapshot
strict StructureMatcher denominator
n_common >= 200
same ALIGNN-FF / CHGNet / MACE-MP denominator
stable-class F1 endpoint unchanged
```

The line reopens only if:

```text
discordance >= 0.40
AND frontier stable-F1 ranking flip exists
```

If the full snapshot still lacks the ranking flip, the NMI discordance line is
permanently closed.

Current readiness: source access is available enough to attempt a future
snapshot export, but the strict primary model set is blocked because ALIGNN-FF
is not currently executable as a same-denominator scorer. A readiness-only
repair attempt confirmed that the official `alignn.ff` Figshare model archives
return HTTP 403 in this environment. The pinned direct-downloader workaround
reported in upstream `usnistgov/alignn` issue #194 was also tried and still
returned HTTP 403 here. A later user-provided local
`v12.2.2024_dft_3d_307k.zip` archive passed zip integrity plus Si and
matched-structure CPU smoke tests, so the local technical scorer gate is now
partially repaired. Route B still requires frozen MP-vs-Alex denominator export
and public/archive provenance for the local ALIGNN-FF model before any primary
claim. AtomGPTLab now provides a public registry entry for the exact checkpoint,
so the provenance status is upgraded to
`PENDING_CLEAN_DOWNLOAD_HASH_MATCH`: public registry gate passed, but clean
download currently returns HTTP 403 in this environment. The endpoint is not
relaxed to CHGNet/MACE-only.

## Route C Alternative Frontier Panel

If ALIGNN-FF remains unavailable as a reproducible arbitrary-structure scorer,
the only allowed alternative is a separate Route C protocol, not a modification
of Route B:

```text
CHGNet
MACE-MP
one frozen third model chosen before outcomes:
SevenNet / MatterSim / Orb / MatGL / M3GNet
```

Route C is currently `protocol_only`; no Route C ranking outcomes have been
inspected for the full MP-vs-Alex denominator. A separate existing-probe
diagnostic has been run on the older 270-row WBM-vs-alex exact-match
denominator and is not a full Route C primary result. Route B remains
unconsumed.

## Route B Runner

`scripts/run_route_b_full_snapshot_rescue.py` implements the frozen Route B
experiment:

```text
MP API-derived records
alex-mp snapshot
strict StructureMatcher denominator
ALIGNN-FF / CHGNet / MACE-MP same denominator
stable-class F1 ranking endpoint
```

The first execution stopped at the MP API data-access gate because `MP_API_KEY`
was not present in the environment. The script does not read credentials from
files or artifacts. After setting `MP_API_KEY` in the shell, rerun:

```bash
python scripts/run_route_b_full_snapshot_rescue.py
```

Route B diagnostic outcome on the minimal `n_common >= 200` MP-vs-alex
denominator:

```text
n_common: 287
overall binary discordance: 0.108
frontier stable-F1 ranking flip: false
go/no-go: NO_GO_keep_NMI_line_closed
```

The refined selection-conditional hypothesis was also tested: discordance did
not concentrate in the top-ranked candidate decile across ALIGNN-FF, CHGNet,
and MACE-MP. This is a no-go for the NMI discordance line under the current
data.

Third-source triangulation was attempted with OQMD on the same strict
MP-vs-Alex denominator. The exact-structure common denominator was too small to
support a three-source claim:

```text
MP-vs-OQMD exact common denominator: 4
Alex-vs-OQMD exact common denominator: 4
claim scope: blocked_or_undercovered_third_source
```

The completed decomposition result is therefore within the MP-vs-Alex
denominator:

```text
overall MP-vs-Alex discordance: 0.108
either-source near-hull 25 meV discordance: 0.146
neither-source near-hull 25 meV discordance: 0.000
```

This localizes the modest full-snapshot discordance at the stability decision
boundary. The earlier WBM-vs-alex/PARC-style 0.522 discordance is retained as a
case-analysis contrast, not as the full-snapshot baseline.

## Claim Boundaries

Allowed:

- “The existing WBM-vs-alex exact-structure probe shows high binary
  exact-stability label discordance.”
- “The primary downstream ranking-flip gate did not pass under the current
  same-denominator frontier-model endpoint.”
- “The completed MP-vs-Alex decomposition localizes discordance near the
  25 meV/atom stability boundary.”

Forbidden:

- “This proves prospective materials discovery.”
- “External DFT databases are interchangeable ground truth.”
- “PARC solves cross-source DFT disagreement.”
- “The NMI discordance paper is launched.”
- “Formula-only matches support the headline discordance number.”
- “OQMD triangulates the MP-vs-Alex result.” The current OQMD exact denominator
  is undercovered.

## Main Files

```text
outputs/milestones/materials_label_discordance_preregistration/
  DATA_ACCESS_GO_NO_GO.md
  ROUTE_B_ONE_SHOT_RESCUE_PROTOCOL.md
  ROUTE_B_READINESS_CLOSEOUT.md
  ROUTE_B_ALIGNN_FF_PROVENANCE_QUALIFICATION.md
  ROUTE_B_ALIGNN_FF_PUBLIC_PROVENANCE_UNLOCK.md
  ROUTE_C_ALTERNATIVE_FRONTIER_PANEL_PROTOCOL.md
  ROUTE_C_EXISTING_PROBE_EXPERIMENT.md
  ALIGNN_FF_ATOMGPTLAB_SOURCE_NOTE.md
  ALIGNN_FF_READINESS_FIX_ATTEMPT.md
  ALIGNN_FF_PINNED_DOWNLOADER_REPAIR.md
  DISCORDANCE_STUDY_PREREGISTRATION.md
  MATERIALS_LABEL_DISCORDANCE_EXPERIMENT_CLOSEOUT.md
  protocol_discordance_study.yaml
  table_alignn_ff_readiness_attempts.csv
  table_alignn_ff_download_integrity.csv
  table_alignn_ff_smoke_tests.csv
  table_route_b_alignn_ff_provenance_checklist.csv
  table_route_b_alignn_ff_eligibility_decision.csv
  table_route_b_alignn_ff_public_provenance_unlock.csv
  table_route_c_frontier_panel_protocol.csv
  table_route_c_go_no_go_gate.csv
  table_route_c_existing_probe_model_scores.csv
  table_route_c_existing_probe_ranking_metrics.csv
  table_route_c_existing_probe_flip_summary.csv
  ROUTE_B_FULL_SNAPSHOT_RESCUE_CLOSEOUT.md
  THIRD_SOURCE_AND_DISCORDANCE_DECOMPOSITION_CLOSEOUT.md
  table_route_b_full_snapshot_data_access_failure.csv
  table_route_b_full_snapshot_matches.csv
  table_route_b_full_snapshot_model_scores.csv
  table_route_b_full_snapshot_ranking_metrics.csv
  table_route_b_full_snapshot_summary.csv
  table_third_source_triangle_summary.csv
  table_discordance_near_hull_decomposition.csv
  table_discordance_chemical_system_top.csv
  table_discordance_element_family.csv
  table_discordance_prototype_proxy.csv
  table_wbm_alex_case_comparison.csv
  table_data_access_smoke.csv
  table_minimal_discordance_probe.csv
  table_frontier_model_scores.csv
  table_downstream_ranking_metrics.csv
  table_downstream_ranking_flip_summary.csv
  table_discovered_count_delta.csv
  MANIFEST_SHA256.txt
```

## Verify

```bash
(cd outputs/milestones/materials_label_discordance_preregistration && sha256sum -c MANIFEST_SHA256.txt)
sha256sum -c MANIFEST_SHA256.txt
pytest -q tests
```

## Secret Policy

Materials Project API keys are never committed. The smoke-check artifact only
records that a query succeeded and redacts all credential material.
