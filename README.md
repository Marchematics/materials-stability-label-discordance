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

The Fig. 4(c) reconciliation bar is now completed:

```text
MP-native exact-stable release set: n=124
MP-vs-Alex discordance on that selected set: 0.169
full MP-vs-Alex denominator discordance: 0.108
WBM-vs-alex existing probe discordance: 0.522
```

A strict SCS/PARC portability check on the 287-row MP-vs-Alex denominator
released zero candidates at alpha=0.10 across all tested budgets, so Fig. 4(c)
is explicitly a source-native release-conditioning diagnostic rather than a new
certified PARC release claim.

Full Alexandria MP-identifier denominator construction has also been run as a
separate public-safe milestone. It does not overwrite the frozen 287-row
Route-B diagnostic:

```text
Alexandria rows with MP identifiers: 43,984
MP records successfully queried: 43,169
strict StructureMatcher matches: 43,139
MP-vs-Alex exact-stability discordance: 5,060 / 43,139 = 0.1173
claim scope: full denominator construction, not a new NMI launch gate
```

This confirms that the full MP-Alex overlap remains a modest source-discordance
regime, close to the smaller MP-Alex diagnostic and far below the preregistered
0.40 NMI-launch threshold.

Submission-readiness diagnostics were added to make the denominator and
benchmark consequences auditable:

```text
Alexandria v20 rows: 675,204
Alexandria rows with MP identifiers: 43,984
frozen Route-B MP-ID candidates attempted: 300
MP records successfully queried: 287
strict StructureMatcher denominator: 287
OQMD exact matches: 4
```

Near-hull uncertainty flags capture all observed MP-vs-Alex binary discordance
on this denominator, at the cost of substantial flag burden:

```text
5 meV either-source flag: captures 31/31 discordant pairs, flags 152/287
25 meV either-source flag: captures 31/31 discordant pairs, flags 213/287
```

The selection-fraction curves and logistic/permutation tests keep the refined
model-selection hypothesis closed: model rank is weak after accounting for
energy-boundary variables, and no tested model shows robust high-score
discordance amplification across selection fractions.

## Claim Boundaries

## Related-Work Positioning

The experimental package is complete enough for the current paper scope; the
next manuscript-facing step is literature positioning rather than another large
benchmark run. `docs/RELATED_WORK_POSITIONING.md` adds ready-to-use paragraphs
that place the result against JARVIS-Leaderboard, Matbench Discovery,
foundation MLIPs, stable-materials prediction and generative materials design.
`docs/bibliography_additions.bib` provides the corresponding citation entries.

Boundary: these references motivate the benchmark-reliability question. They
do not introduce new GRACE, MatterGen, SevenNet, Orb, MatterSim or full
Matbench Discovery experiments.

## Benchmark Reliability Enhancement

`outputs/milestones/benchmark_reliability_enhancement/` adds completed
full-denominator reporting enhancements on top of the 43,139 strict
MP-Alexandria matches:

```text
full denominator discordance: 5,060 / 43,139 = 0.1173
MP-exact-stable selected subset discordance: 0.2150
Alex-exact-stable selected subset discordance: 0.0976
5 meV either-source near-hull flag: captures 5,060 / 5,060 discordant pairs,
  flags 21,354 / 43,139 structures
```

The same milestone adds a source-aware benchmark card and a 24-row materials
case atlas. It also freezes, but does not claim as completed, three gated
protocols: common-hull/common-competitor mechanism decomposition, third-source
formula-query triangulation, and full-denominator model benchmark-impact
analysis. These protocols are claim boundaries, not completed evidence.

## Common-Composition Hull Proxy Boundary

`outputs/milestones/common_hull_mechanism_subset/` converts the common-hull
idea from protocol-only into a deterministic coverage-boundary experiment. It
samples 1,000 native MP-Alex discordant structures plus 500 concordant controls
and attempts a common-composition competitor-hull proxy using public MP
formation energies and Alexandria formation-energy proxies.

The result is deliberately **not** a positive mechanism-decomposition claim:

```text
discordant mechanism sample: 10 / 1,000 common-composition proxy available
concordant controls: 6 / 500 common-composition proxy available
claim scope: coverage-boundary result, not full common-hull reconstruction
```

This failed coverage gate is useful because it shows that mechanism attribution
cannot be obtained by a lightweight public-table join. A paper-facing mechanism
claim would require dedicated common-hull reconstruction with broader
competitor coverage and unclipped/source-compatible formation energies.

## Benchmark Impact of Label-Source Choice

`outputs/milestones/benchmark_impact_label_source_choice/` adds a completed
benchmark-impact result on the full 43,139 strict MP-Alex denominator. This is
not a full-denominator ML leaderboard; it is a source-label transfer and
source-native ranking reference that quantifies what label-source choice alone
can do to benchmark conclusions.

```text
MP source-native perfect labeler evaluated by Alexandria:
  F1 = 0.8396, accuracy = 0.8827
  F1 drop from source-native self-evaluation = -0.1604

MP-stable candidates rejected by Alexandria:
  3,628 / 16,872 = 0.2150

Alexandria-stable candidates rejected by MP:
  1,432 / 14,676 = 0.0976

source-agreement-only denominator retained:
  38,079 / 43,139 = 0.8827
```

The paper-facing claim is therefore: even before asking which ML model is
better, source-native stability labels impose a measurable benchmark
uncertainty band. The milestone does not claim that CHGNet, MACE-MP,
ALIGNN-FF, GRACE or any other model ranking flips on the full denominator.

## Model-Facing Sensitivity Check

`outputs/milestones/model_facing_benchmark_sensitivity_check/` adds the minimal
real-model diagnostic requested for the paper: one true CHGNet ranking on a
deterministic 5,000-structure subset of the 43,139 strict MP-Alex denominator.
The score is a CHGNet formation-energy proxy built from CHGNet structure
energies and MP elemental references.

```text
model: CHGNet
scored denominator: 5,000 strict MP-Alex matched structures
score: negative CHGNet formation-energy proxy
device: CUDA

precision@100:
  MP labels: 0.370
  Alexandria labels: 0.340
  MP-minus-Alex shift: +0.030

precision@300:
  MP labels: 0.333
  Alexandria labels: 0.290
  MP-minus-Alex shift: +0.043

AUROC:
  MP labels: 0.454
  Alexandria labels: 0.466

score-direction sanity:
  raw formation-energy proxy as higher-is-stable AUROC: 0.546 / 0.534
  negative formation-energy proxy as higher-is-stable AUROC: 0.454 / 0.466

top-K decomposition at K=300:
  both stable: 77
  MP-only stable: 23
  Alex-only stable: 10
  both unstable: 190
  bootstrap CI for MP-minus-Alex precision shift: [0.0067, 0.0800]
```

This is intentionally not a leaderboard: CHGNet is used only to show that the
label-source effect is visible under a real model ranking on a large subset,
not only under source-native oracle labels. The diagnostic should be described
as a model-facing sensitivity check, not as evidence that CHGNet is a strong
predictor on this denominator. The direction-sanity table is reported to rule
out a hidden sign convention error; neither direction is promoted as a
composition-aware hull-distance predictor.

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
  FIG4C_SELECTION_CONDITIONED_MP_ALEX_CLOSEOUT.md
  SUBMISSION_READY_DIAGNOSTICS_CLOSEOUT.md
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
  table_fig4c_selection_conditioned_mp_alex.csv
  table_fig4c_scs_portability_check.csv
  table_fig4_reconciliation_bars.csv
  table_denominator_construction_audit.csv
  table_representativeness_num_sites_distribution.csv
  table_representativeness_element_frequency.csv
  table_representativeness_crystal_system.csv
  table_representativeness_ehull_distribution.csv
  table_representativeness_stable_fraction.csv
  table_wbm_alex_probe_formal_definition.csv
  table_wbm_alex_probe_formal_summary.csv
  table_uncertainty_threshold_sweep.csv
  table_benchmark_metrics_uncertainty_filtered.csv
  table_benchmark_ranking_stability_uncertainty_filtered.csv
  table_selection_fraction_discordance_curve.csv
  table_logistic_regression_discordance.csv
  table_model_rank_permutation_tests.csv
  table_mp_alex_ehull_scatter_source.csv
  table_top_discordant_structures_by_delta_ehull.csv
  table_third_source_coverage_closeout.csv
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
