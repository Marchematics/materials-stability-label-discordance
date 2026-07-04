# Route B ALIGNN-FF Provenance Qualification

## Purpose

This document qualifies whether the local ALIGNN-FF archive can support Route B
primary evidence.

Route B requires:

```text
legal reproducible ALIGNN-FF scorer
or frozen public ALIGNN-FF predictions
with checksum / version / source recorded
```

This qualification does not run the one-shot MP-vs-Alex full-snapshot rescue.

## Local Archive

```text
path: /root/v12.2.2024_dft_3d_307k.zip
size_bytes: 549019
sha256: ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5
zip_ok: true
```

Internal files:

```text
v12.2.2024_dft_3d_307k/
v12.2.2024_dft_3d_307k/best_model.pt
v12.2.2024_dft_3d_307k/config.json
v12.2.2024_dft_3d_307k/history_train.json
v12.2.2024_dft_3d_307k/history_val.json
```

Important internal hashes:

```text
best_model.pt: f47f3d231605d58c21538ee5a3d1fe5c7f7711d9cd31deb6964965e23f84b269
config.json: ac194348870c6d584ab95da25c2e51b27856625326398de7d6dfe825295164cf
history_train.json: ee05ff4dbd477b39c09f8458ff67f5935f32663469db382bd04dab0d9a9009bd
history_val.json: 828eb1157b1b6c2fa0c8839d8db6e396d7c420fa9a5f30cf40c0458001967e2f
```

Config identifiers:

```text
config version: af3ae5d1c5711ef9cad6cf930de78f30e6627382
dataset: user_data
target: target
model folder: v12.2.2024_dft_3d_307k
```

## Software Environment

```text
Python: 3.12.4
alignn: 2026.4.2
jarvis: 2026.4.2
torch: 2.8.0+cu128
dgl: 2.1.0
CUDA available: true
device used for smoke tests: cpu
```

CPU was used because the installed DGL build does not expose CUDA device APIs
in this environment.

## Smoke Tests

The local archive passed:

```text
Si diamond smoke:
  natoms: 2
  energy_eV: -7.9507317543029785
  energy_per_atom: -3.9753658771514893
  max_abs_force: 2.3259781301021576e-07

matched-structure smoke:
  material_id: wbm-1-10155
  formula: Cl6 Mn2
  natoms: 8
  energy_eV: -17.957056045532227
  energy_per_atom: -2.2446320056915283
```

## Acquisition Source Assessment

Known facts:

- `atomgptlab/alignn` documentation lists `v12.2.2024_dft_3d_307k` as an
  available ALIGNN-FF checkpoint folder and documents explicit local checkpoint
  paths as a supported usage pattern.
- The installed `alignn` package exposes the same model name through
  `alignn.ff.ff.get_all_models()`.
- The official Figshare downloader URLs tested in this environment return
  `HTTP 403` and could not be used to reproduce the archive download.
- The archive currently exists as a local file supplied at `/root`.

Acquisition source classification:

```text
public registry entry exists via atomgptlab/alignn
local archive supplied by user
clean download hash match pending because registry URL returns HTTP 403 in this environment
```

## Eligibility Decision

```text
technical scorer eligibility: PASS
public registry eligibility: PASS
clean download hash match: PENDING_BLOCKED_403
Route B primary evidence eligibility: PENDING_HASH_MATCH
```

Reason:

The archive is a valid local model artifact and the scorer works. A public
registry and documentation now identify the same checkpoint. However, the
registry download does not yet reproduce the local archive in this environment
because the Figshare URL returns `HTTP 403`. Therefore Route B cannot yet use
this local archive for primary manuscript evidence.

## Required Action To Convert To PASS

One of the following must be completed before running Route B as primary
evidence:

1. restore a working official public download URL and record its checksum;
2. archive the exact zip in a reviewable artifact store with license/source
   notes and checksum; or
3. provide frozen public ALIGNN-FF predictions covering the full Route B
   denominator with source and checksum.

Until then:

```text
Route B remains blocked for primary evidence.
The local archive may be used only for internal diagnostic scoring.
```
