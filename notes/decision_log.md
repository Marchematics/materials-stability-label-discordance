# Decision Log

Last updated: 2026-05-26.

## Durable Decisions

1. **Venue and article type**
   - Target `npj Computational Materials` as an Article.
   - Use Nature Portfolio / Springer Nature article style.

2. **Dominant contribution**
   - Frame the paper as a source-native public-label benchmark-reliability audit
     and reporting framework, not as a new model, new DFT workflow or general
     indictment of public databases.

3. **Primary denominator**
   - Primary analysis uses the full MP--Alexandria MP-identifier exact-match
     denominator: 43,139 strict matches retained from 43,984 Alexandria rows
     carrying MP identifiers.
   - The denominator is a queryable MP-ID overlap, not a random all-source
     intersection.

4. **Old 287-structure subset**
   - The 287-structure set is no longer a primary denominator.
   - It appears only as a scored diagnostic / supplementary selection
     diagnostic where full-denominator model scores are unavailable.

5. **Near-hull flags**
   - In the clipped public-label representation, either-source near-hull flags
     mechanically capture discordant pairs at positive thresholds because stable
     entries are reported at zero.
   - Therefore near-hull flags are reporting-burden diagnostics, not independent
     evidence for physical localization.

6. **CHGNet diagnostic**
   - The CHGNet 5,000-structure result is a fixed-ranking label-source
     sensitivity check.
   - It should not be described as CHGNet stability performance or a
     Matbench-Discovery-style leaderboard.

7. **WBM--Alexandria probe**
   - Retain as a supplementary selection-conditioned diagnostic.
   - Do not use it as a generic DFT-label discordance rate.

8. **Data/code release**
   - Use Zenodo concept DOI `10.5281/zenodo.20392665` in the manuscript and
     availability statements so the citation resolves to the latest version.
   - The checked published version record is `10.5281/zenodo.20392666`.
   - Use public repository URL
     `https://github.com/Marchematics/materials-stability-label-discordance`.
   - Zenodo release packages should be data/code support packages, not
     manuscript archives: exclude manuscript text/PDF files, cover letters,
     raw MP API caches and internal exploratory decision documents.

9. **References**
   - Use the user-confirmed `npj.bib` as the base bibliography.
   - `hegde2023quantifying` was explicitly restored after the user supplied the
     BibTeX entry.
