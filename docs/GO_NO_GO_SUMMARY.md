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

Provenance decision update: AtomGPTLab provides a public registry and
documentation for the exact `v12.2.2024_dft_3d_307k` checkpoint. Therefore the
public registry gate is now PASS. The clean-download hash-match gate remains
PENDING because the registry URL still returns HTTP 403 in this environment.
Until the registry download reproduces the local archive hash, or the exact zip
is archived through a reviewable mirror, Route B remains pending and the local
archive is internal-diagnostic only.

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

## Route B Runner Status

Status: runner implemented; first execution blocked at MP API data access.

The Route B full-snapshot runner requires `MP_API_KEY` in the shell
environment. This is intentional: credentials are not read from files and are
not committed to artifacts. The first execution produced
`table_route_b_full_snapshot_data_access_failure.csv` and did not consume the
one-shot scientific outcome.

After local credential configuration, the Route B diagnostic completed on a
minimal qualified MP-vs-alex denominator:

| Item | Value |
|---|---:|
| strict matches | 287 |
| overall MP-vs-alex discordance | 0.108 |
| stable-F1 ranking flip | false |
| max absolute F1 delta | 0.0288 |

Result: no-go for the original Route B launch rule.

## Selection-Conditional Discordance

Status: no-go.

The refined hypothesis asked whether discordance concentrates in the
model-selected high-confidence region. It does not on the Route B denominator:

| Model | top-decile discordance | enrichment over baseline |
|---|---:|---:|
| ALIGNN-FF | 0.172 | 1.60 |
| CHGNet | 0.103 | 0.96 |
| MACE-MP | 0.103 | 0.96 |

Gate result: `NO_GO`. The NMI discordance line remains closed.

## Third-Source Triangulation

Status: attempted but undercovered.

OQMD was added as a third-source exact-structure join attempt on the same
MP-vs-Alex strict denominator. It does not support a completed three-source
measurement:

| Comparison | Exact common denominator | Claim scope |
|---|---:|---|
| MP vs Alex | 287 | completed pairwise baseline |
| MP vs OQMD | 4 | blocked / undercovered third source |
| Alex vs OQMD | 4 | blocked / undercovered third source |

Interpretation: OQMD cannot currently be used as a third independent
full-denominator measurement for this artifact. These rows must remain
coverage-boundary diagnostics and cannot be used as positive triangulation.

## Discordance Source Decomposition

Status: completed MP-vs-Alex decomposition.

The overall MP-vs-Alex discordance is modest, but it is concentrated at the
stability boundary:

| Band | n | Discordant | Discordance |
|---|---:|---:|---:|
| either source near hull within 25 meV/atom | 213 | 31 | 0.146 |
| neither source near hull within 25 meV/atom | 74 | 0 | 0.000 |
| MP near hull within 25 meV/atom | 198 | 29 | 0.146 |
| Alex near hull within 25 meV/atom | 196 | 24 | 0.122 |

Interpretation: the durable result is not an NMI-launching high-discordance
finding. It is a more modest label-boundary result: binary stable/unstable
calls disagree primarily near the hull, while the high-score ML selection
amplification hypothesis remains a no-go.

## WBM-vs-Alex Case Analysis

Status: case-analysis contrast.

The earlier WBM-vs-alex/PARC-style probe remains important because it explains
why the stronger NMI hypothesis was plausible:

| Case | n | Discordance | Role |
|---|---:|---:|---|
| WBM-vs-alex existing probe | 270 | 0.522 | high-discordance case analysis |
| MP-vs-alex full snapshot | 287 | 0.108 | full-snapshot baseline |

Interpretation: the 0.522 observation should be discussed openly as a
selection/source-specific case, not hidden and not generalized.

## Fig. 4(c): Selection-Conditioned MP-vs-Alex Reconciliation

Status: completed diagnostic.

The source-native MP release rule was applied to the MP-vs-Alex exact-match
denominator:

| Bar | n | Discordance | Role |
|---|---:|---:|---|
| WBM-vs-alex existing probe | 270 | 0.522 | case-analysis high-discordance probe |
| MP-vs-Alex full denominator | 287 | 0.108 | full denominator baseline |
| MP-native exact-stable selected set | 124 | 0.169 | Fig. 4(c) selection-conditioned bar |
| MP-native 25 meV near-hull set | 198 | 0.146 | sensitivity |

Interpretation: conditioning on the MP-native stable-release set increases
discordance relative to the full MP-vs-Alex denominator, but only modestly and
far below the 0.522 WBM-vs-alex case. The reconciliation is therefore mostly a
source-pair / denominator effect, with a smaller MP-native selection effect.

A strict SCS/PARC portability check on this small denominator produced zero
non-empty releases at `alpha=0.10`, so this panel is not a certified PARC
release claim.
