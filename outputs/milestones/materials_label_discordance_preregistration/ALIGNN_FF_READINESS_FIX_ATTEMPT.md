# ALIGNN-FF Readiness Fix Attempt

## Scope

This record addresses only the Route B blocker named in the preregistered
rescue protocol:

```text
legal reproducible ALIGNN-FF scorer
or frozen public ALIGNN-FF predictions
with checksum / version / source recorded
```

No Route B endpoint, denominator, label definition, metric, or model set was
changed. No MP-vs-Alex full rescue outcome was generated.

## Official scorer attempt

The installed `alignn` package exposes official ALIGNN-FF model names through
`alignn.ff.ff.get_all_models()` and uses `get_figshare_model_ff()` to retrieve
model archives from Figshare. The default scorer path is:

```text
v12.2.2024_dft_3d_307k
```

The current execution environment cannot retrieve the official model archives:
the tested Figshare file URLs return `HTTP 403` HTML responses rather than zip
archives. This reproduces the earlier `BadZipFile` readiness failure and leaves
the locally executable arbitrary-structure ALIGNN-FF scorer unavailable.

A follow-up pinned-downloader repair was also attempted after checking the
upstream `usnistgov/alignn` issue #194, which reports the same `BadZipFile`
failure and suggests the direct `ndownloader.figshare.com/files/...` URL form.
In this environment, both the direct downloader form and the original
`figshare.com/ndownloader/files/...` form still returned `HTTP 403` HTML
responses, so no valid model archive was obtained.

Tested official model names:

```text
v12.2.2024_dft_3d_307k
v10.30.2024_dft_3d_307k
v8.29.2024_dft_3d
alignnff_wt10
alignnff_fmult
```

## Frozen prediction table found

A local frozen Matbench Discovery / WBM ALIGNN-FF prediction table is available:

```text
path: /home/waas/paper_experiments/data/matbench_discovery/2023-07-11-alignn-ff-wbm-IS2RE.csv.gz
rows: 256963
columns: material_id,e_form_per_atom_alignn_ff
sha256: dc75be97f3bce3ce724680065abf11a19bdc6a3928fdd77ccb42d3f62a02e593
```

This table is legally useful as a frozen public prediction source for
WBM/Matbench `material_id` denominators. It is not an arbitrary-structure
ALIGNN-FF scorer and cannot by itself score a full MP-vs-Alex exact-match
snapshot denominator.

## Route B readiness decision

Route B remains blocked for the full MP-vs-Alex snapshot rescue unless one of
the following becomes true before consuming the one-shot rescue:

1. an official ALIGNN-FF model archive is legally retrievable and smoke-tested
   as an arbitrary-structure scorer; or
2. the frozen primary denominator is restricted, without changing the
   preregistered protocol, to structures that already have frozen public
   ALIGNN-FF predictions with recorded checksums.

Because the current Route B protocol asks for an MP full snapshot/API-derived
record set versus an independently downloaded Alexandria/alex-mp snapshot, the
WBM-only prediction table is recorded as a partial readiness artifact, not as a
complete fix.

Current status:

```text
ALIGNN-FF arbitrary-structure scorer: local CPU smoke pass from user-provided archive
ALIGNN-FF WBM frozen predictions: available with checksum
Route B full-snapshot primary endpoint: still blocked pending MP snapshot and archive provenance freeze
NMI discordance line: remains closed until the primary model-denominator gate is complete
```
