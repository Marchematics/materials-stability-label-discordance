# ALIGNN-FF Pinned Downloader Repair

## Purpose

This is a readiness-only repair attempt for the frozen Route B blocker:

```text
legal reproducible ALIGNN-FF scorer
or frozen public ALIGNN-FF predictions
with checksum / version / source recorded
```

The Route B protocol was not changed and the one-shot MP-vs-Alex full rescue
was not run.

## Upstream issue

The ALIGNN-FF `BadZipFile` failure is consistent with the upstream
`usnistgov/alignn` issue titled `Invalid zip files downloaded from figshare`
(issue #194). That report identifies the failure at initialization of
`AlignnAtomwiseCalculator`, where `default_path()` downloads
`v12.2.2024_dft_3d_307k.zip` and then fails because the file is not a valid
zip. The report states that switching from the `figshare.com/ndownloader`
form to the direct `ndownloader.figshare.com/files/...` form worked in that
environment.

The repair attempted that direct downloader form, plus the original form and a
download-query variant, without changing the model identity.

## Local environment

```text
python: 3.12.4
alignn: 2026.4.2
jarvis-tools import path: jarvis 2026.4.2
torch: 2.8.0+cu128
dgl: 2.1.0
```

## Download integrity result

All tested URLs returned `HTTP 403` with an HTML body, not a zip archive.
The response body was 118 bytes and had SHA256
`58bf2215b395dcac74c009aa98701854e43cbe54a1cd3a95fee6a647ca9910d4`.

No model archive was committed.

## Smoke-test result

Because the pinned model archive could not be obtained, no valid
`best_model.pt` / `config.json` directory exists for
`AlignnAtomwiseCalculator(path=...)`. Therefore:

```text
Si smoke test: not run, blocked by missing valid model archive
matched-structure smoke test: not run, blocked by missing valid model archive
10-structure batch smoke: not run, blocked by missing valid model archive
```

## Decision

The pinned downloader repair does not clear the Route B gate in this
environment. Route B remains blocked unless a legal ALIGNN-FF model archive is
obtained and passes integrity plus smoke tests, or unless frozen public
ALIGNN-FF predictions cover the full preregistered denominator without
changing the protocol.

## Local Archive Follow-Up

A local archive was later provided at:

```text
/root/v12.2.2024_dft_3d_307k.zip
```

It passed zip integrity:

```text
size_bytes: 549019
sha256: ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5
contains: best_model.pt, config.json, history_train.json, history_val.json
```

After extraction to `/root/alignn_ff_models/v12.2.2024_dft_3d_307k`, explicit
local-path initialization worked with `device="cpu"`:

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

This clears the local technical scorer smoke gate. It does not by itself
establish public reproducibility of Route B until the archive provenance is
publicly citable or otherwise archived with the artifact package.
