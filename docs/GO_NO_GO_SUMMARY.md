# Go/No-Go Summary

## Step 0: Data Access

Status: partial pass.

Materials Project API smoke query passed for `mp-149`, returning `Si` with
`energy_above_hull=0.0`. This establishes API connectivity only. A full paper
launch still requires frozen source snapshots and hashes.

## Step 1: Minimal Discordance Probe

Status: pass for the existing WBM-vs-alex exact-structure probe.

| Item | Value |
|---|---:|
| exact/high-confidence matched structures | 270 |
| binary exact-stability discordance | 0.522 |
| preregistered launch-signal threshold | 0.400 |

Interpretation: strong evidence that the existing exact-match subset contains
substantial source-dependent binary stability labels.

Boundary: this is not yet the final MP-vs-alex full-snapshot claim.

## Step 2: Downstream Conclusion Flip

Status: primary no-go under the current endpoint.

The primary frontier-model endpoint used ALIGNN-FF, CHGNet and MACE-MP on the
same 270-structure denominator. Stable-class F1 ranking did not materially
flip between WBM and alex-mp labels.

| Endpoint | Status |
|---|---|
| primary frontier stable-F1 ranking flip | no-go |
| auxiliary ALIGNN/CGCNN/MEGNet ranking diagnostic | auxiliary only |
| discovered-count changes | supporting only |

Interpretation: the discordance signal is real on this probe, but the current
primary downstream-consequence gate is not strong enough to launch an NMI
paper by itself.

## Route B: Final Rescue

Only one rescue remains open: MP-vs-Alex full snapshot with strict
StructureMatcher matches, `n_common >= 200`, and the same ALIGNN-FF / CHGNet /
MACE-MP stable-class F1 endpoint. The line reopens only if both discordance is
at least 0.40 and the frontier ranking flips. Otherwise the NMI line is
permanently closed.

Current status: Route B is blocked before outcome generation because the
same-denominator primary model set cannot yet be assembled with ALIGNN-FF.
CHGNet/MACE-only is not an allowed substitute.

## ALIGNN-FF Readiness Repair Attempt

Status: partial only, not a full Route B fix.

The installed `alignn` package exposes official ALIGNN-FF model archives via
Figshare, but the tested model URLs currently return HTTP 403 in this
environment. This leaves the arbitrary-structure ALIGNN-FF scorer blocked.
The direct downloader workaround reported in upstream `usnistgov/alignn` issue
#194 was also tested and returns HTTP 403 here, so the pinned local model-path
repair could not be completed.

Follow-up: a local `/root/v12.2.2024_dft_3d_307k.zip` archive was provided and
passed zip integrity plus explicit local-path CPU smoke tests for Si and one
matched WBM structure. This clears the local technical scorer smoke gate, but
Route B still needs public/archive provenance for that model archive and a
frozen MP-vs-Alex denominator before the one-shot outcome can be claimed.

A frozen Matbench Discovery / WBM ALIGNN-FF prediction table is available:

| Item | Value |
|---|---|
| file | `2023-07-11-alignn-ff-wbm-IS2RE.csv.gz` |
| rows | 256,963 |
| SHA256 | `dc75be97f3bce3ce724680065abf11a19bdc6a3928fdd77ccb42d3f62a02e593` |

Interpretation: the frozen prediction table can support WBM-denominator
diagnostics, but it is not an arbitrary-structure scorer for a full MP-vs-Alex
snapshot. Route B remains blocked unless a legal ALIGNN-FF scorer becomes
available or the preregistered denominator can be satisfied by frozen public
ALIGNN-FF predictions without changing the protocol.

## Route C: Alternative Frontier Panel

Status: protocol-only for full MP-vs-Alex Route C; existing-probe diagnostic
completed on the older WBM-vs-alex denominator.

Route C is allowed only as a separate protocol if ALIGNN-FF remains unavailable.
It is not a modification of Route B, and Route B remains blocked and
unconsumed.

Frozen Route C candidate panel:

| Role | Models |
|---|---|
| required | CHGNet, MACE-MP |
| choose one before outcomes | SevenNet, MatterSim, Orb, MatGL, or M3GNet |

The NMI line reopens under Route C only if the same exact/high-confidence
denominator has `n_common >= 200`, binary exact-stability discordance remains
at least 0.40, and the alternative-frontier stable-class F1 ranking flips with
the preregistered effect-size rule. CHGNet/MACE-only results are reduced-panel
diagnostics, not full primary frontier-panel evidence.

Existing-probe outcome: CHGNet / MACE-MP / M3GNet all scored the same 270
WBM-vs-alex exact-match structures, but stable-class F1 ranking did not flip.
This is a diagnostic no-go for that existing denominator, not a full Route C
full-snapshot result.
