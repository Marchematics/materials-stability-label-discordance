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
returned HTTP 403 here. A frozen WBM/Matbench ALIGNN-FF prediction table is
available and checksummed, but it does not score arbitrary MP-vs-Alex snapshot
structures. The endpoint is not relaxed to CHGNet/MACE-only.

## Claim Boundaries

Allowed:

- “The existing WBM-vs-alex exact-structure probe shows high binary
  exact-stability label discordance.”
- “The primary downstream ranking-flip gate did not pass under the current
  same-denominator frontier-model endpoint.”

Forbidden:

- “This proves prospective materials discovery.”
- “External DFT databases are interchangeable ground truth.”
- “PARC solves cross-source DFT disagreement.”
- “The NMI discordance paper is launched.”
- “Formula-only matches support the headline discordance number.”

## Main Files

```text
outputs/milestones/materials_label_discordance_preregistration/
  DATA_ACCESS_GO_NO_GO.md
  ROUTE_B_ONE_SHOT_RESCUE_PROTOCOL.md
  ROUTE_B_READINESS_CLOSEOUT.md
  ALIGNN_FF_READINESS_FIX_ATTEMPT.md
  ALIGNN_FF_PINNED_DOWNLOADER_REPAIR.md
  DISCORDANCE_STUDY_PREREGISTRATION.md
  MATERIALS_LABEL_DISCORDANCE_EXPERIMENT_CLOSEOUT.md
  protocol_discordance_study.yaml
  table_alignn_ff_readiness_attempts.csv
  table_alignn_ff_download_integrity.csv
  table_alignn_ff_smoke_tests.csv
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
