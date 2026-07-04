# Route B ALIGNN-FF Public Provenance Unlock

## Status

```text
public registry gate: PASS
clean download hash match: PENDING / currently blocked by HTTP 403
Route B primary evidence gate: PENDING_HASH_MATCH
Route B one-shot outcome: unconsumed
```

## Public Source

The `atomgptlab/alignn` repository provides a public ALIGNN / ALIGNN-FF source
line for the Route B checkpoint.

Public documentation:

```text
repository: https://github.com/atomgptlab/alignn
pretrained ALIGNN-FF docs: https://raw.githubusercontent.com/atomgptlab/alignn/main/docs/pretrained/alignn-ff.md
ASE calculator docs: https://github.com/atomgptlab/alignn/blob/main/docs/usage/ase-calculator.md
```

Registry:

```text
path: alignn/ff/all_models_alignn_atomwise.json
raw URL: https://raw.githubusercontent.com/atomgptlab/alignn/main/alignn/ff/all_models_alignn_atomwise.json
registry SHA256: 07c000c8be735b78e0032c5cec980afd5368ed5c3e74b926316c09a91b15d04f
```

Checkpoint:

```text
model name: v12.2.2024_dft_3d_307k
registry URL: https://ndownloader.figshare.com/files/50904240
```

## Clean-Room Download Attempt

The registry URL was re-tested as a clean download attempt in this environment.
It returned:

```text
status_code: 403
content_type: text/html
size_bytes: 118
sha256: 58bf2215b395dcac74c009aa98701854e43cbe54a1cd3a95fee6a647ca9910d4
zip_ok: false
```

Therefore the clean-room hash match against the local archive is still pending.

Expected local archive hash:

```text
/root/v12.2.2024_dft_3d_307k.zip
sha256: ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5
```

## Eligibility Decision

The blocker is no longer a pure local-provenance blocker: a public model
registry and documentation exist for the checkpoint identity and intended
local-path usage.

However, Route B does not become primary-evidence executable until a clean-room
download from the public registry reproduces the local archive hash, or until
the exact local archive is made available through a public/citable artifact
mirror.

Current decision:

```text
technical_scorer_gate: PASS
public_registry_gate: PASS
clean_download_hash_match: PENDING
route_b_primary_evidence_gate: PENDING_HASH_MATCH
```

## Required PASS Condition

Route B may be reopened only when:

```text
downloaded archive SHA256 == ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5
AND zip integrity passes
AND internal best_model.pt/config.json hashes match the local archive
```

Until then, the local archive remains usable only for internal diagnostic
scoring, not primary manuscript evidence.
