# Paper Handoff

Last updated: 2026-05-26.

This handoff is for continuing manuscript/package development without relying
on chat history.

## Active Project State

- Repository root: `/Users/nathmath/projectVscode/discordance `.
- Current branch: `npj-submission-v1`.
- Active manuscript source: `manuscript/main.tex`.
- Current compiled manuscript: `manuscript/main.pdf`.
- Bibliography source: `manuscript/references.bib`.
- Confirmed release DOI in text and package: `10.5281/zenodo.20392665`.
- This is the Zenodo concept DOI and should be cited for all versions.
- Current checked Zenodo version record: `10.5281/zenodo.20392666`.
- Public repository URL in Data/Code availability:
  `https://github.com/Marchematics/materials-stability-label-discordance`.
- Current Zenodo-ready data/code release zip:
  `releases/zenodo/discordance-npjcompmat-data-code-2026-05-26.zip`.
- Previous publication-package zip, now superseded for Zenodo upload:
  `releases/zenodo/discordance-npjcompmat-publication-2026-05-23.zip`.
- Latest recorded zip SHA256:
  `81e7ec4000c9cf1f01bc67f670e18c69e0268ad8ea209fd56cc2fc0b5f1c2d97`.
- Current manuscript-upload zip:
  `submission/npj/manuscript_upload_2026-05-26.zip`.
- Current manuscript-upload zip SHA256:
  `f97c00d6e954d6323ab69c3acb445f904b957063371c1a5e1422db48952ea8d0`.

## Manuscript Status

Target venue: `npj Computational Materials`.

Contribution type: benchmark-reliability audit / reporting framework.

Current Results structure:

1. `Full MP--Alexandria MP-identifier exact matching defines the comparison denominator`
2. `Overall and chemistry-stratified source-native discordance`
3. `Cross-source hull-energy differences and reporting burden`
4. `Label-source choice shifts oracle and CHGNet benchmark readouts`

The old main-text defense section has been compressed to one sentence pointing
to `manuscript/supplementary/supplementary_note_1_secondary_diagnostics.md`.

## Current Core Claims

- The full MP--Alexandria MP-ID exact-match denominator contains 43,139 strict
  structure matches.
- Source-native binary stability-label discordance is 5,060/43,139 = 11.7%.
- Cluster bootstrap by chemical system gives a 95% interval of 11.3--12.1%.
- Discordance is chemically nonuniform and enriched at larger cross-source
  hull-energy differences.
- Near-hull flags are reporting-burden diagnostics in the clipped public-label
  representation.
- Label-source choice creates measurable benchmark-readout differences under
  a perfect source-label oracle and a fixed CHGNet 5,000-structure ranking.

## Current Display Items

- Fig. 1: `manuscript/figures/fig1_pipeline.pdf`
  - source denominator and binary label outcomes.
- Fig. 2: `manuscript/figures/fig2_delta_e.pdf`
  - `Delta e` stratification and near-hull reporting burden.
- Fig. 3: `manuscript/figures/fig3_benchmark_impact.pdf`
  - oracle label-transfer, CHGNet precision shifts, top-K decomposition.
- Fig. 4: `manuscript/figures/fig4_chemical_stratification.pdf`
  - chemistry-stratified discordance.
- Table 1: denominator construction audit.
- Table 2: chemistry-stratified discordance.

## Files And Commands To Trust

Regenerate figures:

```bash
python scripts/build_manuscript_figures.py
```

Compile manuscript:

```bash
/opt/homebrew/bin/tectonic -X compile --keep-intermediates --keep-logs manuscript/main.tex
```

Run tests:

```bash
pytest -q tests
```

Check citation-key coverage:

```bash
python - <<'PY'
import re
from pathlib import Path
tex = Path('manuscript/main.tex').read_text()
bib = Path('manuscript/references.bib').read_text()
ckeys = sorted(set(k.strip() for m in re.finditer(r'\\cite\{([^}]+)\}', tex) for k in m.group(1).split(',')))
bkeys = set(re.findall(r'^@\w+\{\s*([^,\s]+)', bib, flags=re.M))
print(f'cited={len(ckeys)} bib={len(bkeys)} missing={sorted(set(ckeys)-bkeys)}')
PY
```

## Most Recent Validation

After adding `hegde2023quantifying` back into `references.bib`:

- cited keys: 52;
- bibliography entries: 61;
- missing citation keys: 0;
- LaTeX/BibTeX scan: no undefined citation, undefined reference, LaTeX error or
  overfull warning;
- `pytest -q tests`: 20 passed;
- data/code-only Zenodo package was rebuilt; it intentionally excludes
  manuscript text/PDF and submission materials.

## Immediate Next Steps

1. If continuing manuscript development, preserve the four-section Results structure.
2. If changing references, rerun the citation-key coverage script and compile.
3. If changing text, keep the title/abstract/Discussion aligned around
   benchmark-reliability, not a general DFT-failure claim.
4. If changing figures or release contents, regenerate the data/code Zenodo zip
   and update its SHA256 in this file.
5. Before submission, run a final submission audit over:
   - `manuscript/main.pdf`;
   - `manuscript/main.tex`;
   - `manuscript/references.bib`;
   - `DATA_AVAILABILITY.md`;
   - `CODE_AVAILABILITY.md`;
   - `submission/npj/cover_letter.md`;
   - the Zenodo zip and manifest.

## Watchouts For The Next Agent

- Do not resurrect the old 287-denominator framing as the primary result.
- Do not present the CHGNet diagnostic as a leaderboard result.
- Do not treat near-hull flags as independent physical localization evidence.
- Do not include local raw Materials Project structure caches in release
  packages.
- Keep old exploratory/internal decision documents out of publication-only
  packages.
- The git worktree may contain many untracked generated artifacts; do not
  blindly reset or clean.
