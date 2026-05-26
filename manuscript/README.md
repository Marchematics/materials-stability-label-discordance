# npj Computational Materials manuscript template

This directory is the working LaTeX manuscript scaffold for the target journal:
`npj Computational Materials`.

## Template source

The local class and bibliography style files come from the official Springer
Nature journal article LaTeX template package, December 2024 version:

- `template_official/springer-nature-latex-template-dec2024.zip`
- `sn-jnl.cls`
- `sn-nature.bst`

Springer Nature describes this as a content-first authoring template that can be
used for Springer Nature journals, including Nature Portfolio journals. The
npj Computational Materials author page also states that initial submissions do
not need to adhere to formatting requirements, and that compiled PDFs are
acceptable before acceptance-stage LaTeX source submission.

## Main files

- `main.tex`: working manuscript scaffold using
  `\documentclass[pdflatex,sn-nature]{sn-jnl}`.
- `references.bib`: bibliography database placeholder.
- `figures/`: local figure exports for manuscript compilation.
- `tables/`: optional source tables or rendered table fragments.
- `supplementary/`: supplementary text and figures.

## Local compile

Use `pdflatex` first. Once citations are added, run BibTeX between LaTeX passes:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

For final submission, keep paths local and avoid subdirectory references if the
submission system requires all LaTeX assets in one directory.
