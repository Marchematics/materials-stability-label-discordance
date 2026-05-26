# npj Computational Materials submission notes

Verified on 2026-05-20 from the journal and Springer Nature author-support
pages.

Primary sources:

- https://www.nature.com/npjcompumats/for-authors-and-referees
- https://www.nature.com/npjcompumats/for-authors-and-referees/submission-guidelines
- https://www.springernature.com/la/authors/campaigns/latex-author-support
- https://support.nature.com/en/support/solutions/articles/6000127538-submit-a-latex-manuscript-to-a-springer-nature-journal-using-overleaf

## Current target

- Journal: `npj Computational Materials`
- Publisher family: Nature Portfolio / Springer Nature
- ISSN: 2057-3960 online
- Working article type: short research article / Article-style manuscript

## Formatting and LaTeX

- Initial submissions to `npj Computational Materials` do not need to adhere to
  the final formatting requirements.
- The journal encourages a single compiled PDF or Microsoft Word file for
  review, with figures inserted near the relevant text or grouped at the end.
- LaTeX source files can be accepted at the acceptance stage; before then,
  supply compiled PDFs.
- Springer Nature recommends the official Springer Nature LaTeX authoring
  template, available as a December 2024 package and via Overleaf.
- For Nature Portfolio journals, use the `sn-nature` template option.
- Keep the source compatible with `pdflatex`.

## Required manuscript sections to keep in the scaffold

- Abstract
- Methods
- Data availability
- Code availability
- Acknowledgements
- Author contributions
- Competing interests
- References in Nature numbered style

## Practical upload constraints

- Check local compilation before upload.
- Avoid custom fonts.
- Convert special characters and diacritics to TeX-safe forms.
- Use local relative figure paths only.
- If the submission system has trouble with `.bib` files, paste the generated
  `.bbl` content into the main `.tex` file before final upload.
