# Zenodo Data/Code Release

Date: 2026-05-26

## Upload Artifact

- Zip: `releases/zenodo/discordance-npjcompmat-data-code-2026-05-26.zip`
- SHA256: `81e7ec4000c9cf1f01bc67f670e18c69e0268ad8ea209fd56cc2fc0b5f1c2d97`
- MD5: `d3e8420d4f863bfa50807e8eb90adf40`
- Size: 9.2 MB
- Package directory:
  `releases/zenodo/discordance-npjcompmat-data-code-2026-05-26/`

## Scope

This is a supporting data/code package for Zenodo. It intentionally excludes:

- `manuscript/main.tex`;
- `manuscript/main.pdf`;
- `manuscript/references.bib`;
- cover letter, significance statement and reviewer checklist;
- local raw Materials Project API caches;
- internal handoff, project-memory and decision-history notes.

It includes:

- full MP--Alexandria denominator outputs;
- chemistry-stratified diagnostics and cluster-bootstrap summaries;
- cross-source hull-energy and near-threshold reporting-burden source tables;
- oracle label-transfer and conflict-exclusion diagnostics;
- CHGNet 5,000-structure sensitivity outputs;
- publication-facing source-data and claim-boundary tables;
- generated figure files and the hand-prepared Fig. 1 source;
- public-safe scripts and data-code package tests;
- README, Data Availability, Code Availability, Reproducibility, release notes,
  manifest and Zenodo metadata draft.

## Validation

- Root repository tests: `pytest -q tests` -> 24 passed.
- Extracted release tests: `pytest -q tests` -> 4 passed.
- Extracted release manifest: `shasum -a 256 -c MANIFEST_SHA256.txt` -> all OK.
- Extracted release figure build:
  `python scripts/build_manuscript_figures.py` -> success.
- Forbidden-file scan before tests found no manuscript main files, submission
  files, `.DS_Store`, `.pytest_cache`, `.git` or raw MP structure cache.
- Package-local README/Data/Code/Reproducibility files use Zenodo concept DOI
  `10.5281/zenodo.20392665`, which resolves to the latest version.

## Zenodo Metadata Recommendation

Current Zenodo record checked: `https://zenodo.org/records/20392666`.

- Version DOI: `10.5281/zenodo.20392666`
- Concept DOI: `10.5281/zenodo.20392665`
- Uploaded file key: `discordance-npjcompmat-data-code-2026-05-26.zip`
- Uploaded-file MD5 seen in the published record on 2026-05-26:
  `113b0ebae0dd03d65a189f4bf8bb5745`
- Current rebuilt local package MD5:
  `d3e8420d4f863bfa50807e8eb90adf40`

Because the published record's uploaded-file MD5 differs from this rebuilt local
package, the remote file should be replaced only if Zenodo still permits file
modification on the record; otherwise create a new Zenodo version under concept
DOI `10.5281/zenodo.20392665`.

Suggested resource type for any future version: `Dataset` or equivalent
data/code package.

Creators:

- Wen, Xinling;
- Zhang, Jiahao;
- Chen, Yu;
- Hou, Yawei, ORCID `0009-0001-3975-2707`.
