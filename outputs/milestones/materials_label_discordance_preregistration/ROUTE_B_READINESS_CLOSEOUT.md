# Route B Readiness Closeout

Route B was frozen as the only allowed rescue:

```text
Materials Project API-derived records
vs independently downloaded Alexandria/alex-mp snapshot
strict StructureMatcher denominator
n_common >= 200
same ALIGNN-FF / CHGNet / MACE-MP denominator
stable-class F1 endpoint unchanged
```

The data-source side is ready enough for a future snapshot export:

- Materials Project API smoke query passed.
- Local `alex_mp_20.zip` exists.

The primary model-denominator gate is not ready:

- CHGNet is locally executable.
- MACE-MP is locally executable.
- ALIGNN-FF is not currently executable as a same-denominator scorer. The
  installed `alignn.ff` default model download attempted
  `v12.2.2024_dft_3d_307k`, but the response was not a valid zip and raised
  `BadZipFile`.

An additional readiness-only repair attempt was made without changing the
Route B protocol. The official ALIGNN-FF Figshare model archives exposed by the
installed `alignn` package currently return `HTTP 403` responses in this
environment for the tested model names
`v12.2.2024_dft_3d_307k`, `v10.30.2024_dft_3d_307k`,
`v8.29.2024_dft_3d`, `alignnff_wt10`, and `alignnff_fmult`.

After checking the upstream `usnistgov/alignn` issue #194, a pinned downloader
repair was attempted with the reported direct downloader pattern
`https://ndownloader.figshare.com/files/50904240`. In this environment the
direct URL, the original `figshare.com/ndownloader/files/50904240` URL, and a
download-query variant all returned `HTTP 403` HTML responses, not model zips.
Therefore explicit local-path initialization cannot yet be smoke-tested.

A frozen Matbench Discovery / WBM ALIGNN-FF prediction table was found and
checksummed:

```text
2023-07-11-alignn-ff-wbm-IS2RE.csv.gz
rows: 256963
sha256: dc75be97f3bce3ce724680065abf11a19bdc6a3928fdd77ccb42d3f62a02e593
```

This table can support WBM-denominator diagnostics, but it is not an
arbitrary-structure scorer for the full MP-vs-Alex snapshot denominator. It is
therefore recorded as partial readiness, not as a complete fix.

Under the frozen Route B protocol, the endpoint cannot be replaced by
CHGNet/MACE-only. Therefore Route B is blocked before the full rescue outcome.
The NMI discordance line remains closed unless a legal, reproducible ALIGNN-FF
scorer becomes available before the one-shot rescue is run.

This closeout does not consume a full Route B outcome because the strict
same-denominator primary model set could not be assembled.
