# Route C Existing-Probe Diagnostic

## Status

```text
completed diagnostic
not full MP-vs-Alex Route C primary
Route B remains unconsumed; full outcome still blocked pending MP snapshot and model-provenance freeze
```

## What Was Run

The alternative-frontier Route C panel was evaluated on the existing
WBM/Matbench-vs-alex exact-structure denominator. This uses the same 270
exact-structure matched rows as the earlier discordance probe.

This is not the full Route C rescue because the full MP API-derived snapshot
denominator was not exported in this run. It is a same-denominator model-panel
diagnostic only.

## Model Panel

```text
CHGNet
MACE-MP
M3GNet-Eform-MP-2018.6.1 via MatGL
```

M3GNet was selected as the third model before computing Route C ranking
outcomes because it is locally executable through MatGL in this environment.

## Lead Result

```text
models eligible: CHGNet|MACE-MP|M3GNet
top model flip: False
ordering flip: False
max absolute stable-F1 delta: 0.0673076923076923
go/no-go: NO_GO_existing_probe_no_material_F1_ranking_flip
claim scope: existing_WBM_vs_alex_probe_only; not full MP-vs-Alex Route C primary
```

## Claim Boundary

This result may be cited only as an existing-probe diagnostic. It cannot reopen
the NMI discordance line by itself because the preregistered Route C full
snapshot denominator has not been constructed. A full Route C result still
requires:

```text
MP API-derived records vs independently downloaded alex-mp snapshot
strict StructureMatcher denominator
n_common >= 200
CHGNet / MACE-MP / frozen third model on the same denominator
discordance >= 0.40
alternative-frontier stable-F1 ranking flip
```
