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
