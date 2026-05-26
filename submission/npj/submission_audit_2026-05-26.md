# npj Computational Materials Submission Audit

Date: 2026-05-26

## Manuscript Upload Package

- Upload file: `submission/npj/manuscript_upload_2026-05-26.zip`
- SHA256: `f97c00d6e954d6323ab69c3acb445f904b957063371c1a5e1422db48952ea8d0`
- Package contents:
  - `main.tex`
  - `sn-jnl.cls`
  - `figures/fig1_pipeline.pdf`
  - `figures/fig2_delta_e.pdf`
  - `figures/fig3_benchmark_impact.pdf`
  - `figures/fig4_chemical_stratification.pdf`
- The upload `main.tex` has the bibliography embedded from `manuscript/main.bbl`
  so the journal compiler does not need to run BibTeX.
- The upload package was extracted into a temporary directory and compiled
  successfully with Tectonic.
- The upload package includes only the four figure PDFs referenced by
  `main.tex`.

## Separate Files Prepared For Later Portal Steps

- Supplementary Information: `submission/npj/supplementary_information_2026-05-26.pdf`
- Cover letter: `submission/npj/cover_letter.md`
- Significance statement: `submission/npj/significance_statement.md`
- Author information: `submission/npj/author_information_2026-05-26.md`
- Reviewer-facing claim-boundary checklist:
  `submission/npj/reviewer_checklist.md`
- Data availability source text: `DATA_AVAILABILITY.md`
- Code availability source text: `CODE_AVAILABILITY.md`

## Validation

- Rebuilt manuscript figures with `python scripts/build_manuscript_figures.py`.
- Ran `pytest -q tests`: 24 passed.
- Citation-key coverage: 52 cited keys, 61 bibliography entries, missing keys 0.
- Updated authorship to Xinling Wen and Jiahao Zhang as equal-contribution
  co-first authors, Yu Chen as corresponding author, and Yawei Hou as third
  author.
- Updated Data/Code availability to Zenodo concept DOI
  `10.5281/zenodo.20392665`.
- Removed the prior AI-assisted writing/manuscript-editing disclosure language;
  the AI disclosure now states use only for data-analysis support,
  computational-check scripting and method/background research.
- Active manuscript compile:
  `/opt/homebrew/bin/tectonic -X compile --keep-intermediates --keep-logs manuscript/main.tex`.
- Fixed the previous BibTeX error for `xie2022crystal` by converting the cited
  conference entry into a `@article`-style entry compatible with
  `sn-nature.bst`.
- Final active compile and extracted upload-package compile have no undefined
  citations, undefined references, LaTeX errors, package errors, overfull boxes
  or BibTeX errors in the log scan.
- Remaining log messages are float-placement warnings and underfull boxes.

## Audit Findings

### High

None found.

### Medium

None blocking the manuscript upload step. The only portal-order dependency is
that Supplementary Note 1 is cited in the manuscript and should be uploaded as a
separate Supplementary Information PDF in the later supplementary-file step.

### Low

- The LaTeX log contains standard float-placement warnings where `[h]` was
  changed to `[ht]`; these do not block compilation.
- The figure PDFs are PDF 1.7 while the output PDF target is 1.5; Tectonic
  includes them successfully and logs this as a warning.

## Claim-Boundary Check

- Main claim remains the full MP--Alexandria denominator:
  43,139 strict matches and 5,060 discordant labels (11.7%).
- The old 287-structure subset is only a scored diagnostic subset.
- CHGNet is framed as a fixed-ranking label-source sensitivity diagnostic, not
  a leaderboard.
- Near-hull flags are framed as reporting-burden diagnostics under clipped
  public labels, not independent physical localization evidence.
- OQMD exact-structure coverage is retained only as a coverage boundary.

## Readiness

The manuscript upload package is ready for the portal's Manuscript file step.
The next highest-leverage check before final submission is to upload the
Supplementary Information PDF and verify that the portal-generated PDF has all
four figures placed and legible.
