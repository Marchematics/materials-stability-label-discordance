# ALIGNN-FF AtomGPTLab Source Note

The `atomgptlab/alignn` repository is the current public home of ALIGNN /
ALIGNN-FF documentation used for this readiness check.

Relevant documented facts:

- the README identifies ALIGNN-FF as the force-field variant and links the
  ALIGNN-FF ASE calculator documentation;
- the ASE calculator documentation uses
  `AlignnAtomwiseCalculator(path=default_path())` and also states that a
  specific local checkpoint folder can be passed directly;
- the pre-trained ALIGNN-FF page lists `v12.2.2024_dft_3d_307k` among available
  checkpoint folders.

Repository / documentation URLs:

```text
https://github.com/atomgptlab/alignn
https://github.com/atomgptlab/alignn/blob/main/docs/usage/ase-calculator.md
https://github.com/atomgptlab/alignn/blob/main/docs/pretrained/alignn-ff.md
```

Local implication:

```text
explicit local path is an intended usage pattern
```

However, this source note does not by itself prove the provenance of the local
`/root/v12.2.2024_dft_3d_307k.zip` archive. The archive has a recorded
checksum and passed smoke tests, but public reproducibility still requires the
archive to be hosted, cited, or otherwise made available under a reviewable
artifact policy.
