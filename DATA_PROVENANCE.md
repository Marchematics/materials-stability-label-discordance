# Data provenance

## Overview

This repository uses structure-matched records from Materials Project,
MatterGen alex-mp-20 and official Alexandria-PBE. The tables record
source-native labels and derived benchmark views for the exact matched rows.

`denominator_d0_formula.parquet` is referred to in the article as the **F0
formula-support catalogue**; its filename is retained for compatibility with
the released checksums.

## MatterGen alex-mp-20 source

The second label source is **MatterGen alex-mp-20**, the distinct Alex-MP
release distributed with Microsoft MatterGen. It is analysed separately from
the official Alexandria-PBE database. The local source archive is:

```text
alex_mp_20.zip
```

from the Microsoft MatterGen data release:

```text
https://github.com/microsoft/mattergen/tree/main/data-release/alex-mp
```

The MatterGen data-release README describes `alex-mp` as the Alex-MP dataset
used to train and fine-tune MatterGen. Its `alex-mp` README states that the data
contain structures from Alexandria and MP-20, with Alexandria-derived structures
filtered and relaxed with PBE DFT to provide consistent energies. For the
training set, structures with more than 20 atoms per unit cell and structures
with energy above hull greater than 0.1 eV atom^-1 are removed.

The archive used here contains:

```text
alex_mp_20/train.csv
alex_mp_20/val.csv
ref.csv
```

The analysis uses `train.csv` and `val.csv`. Relevant fields include:

- `material_id`
- `reduced_formula`
- `space_group`
- `chemical_system`
- `num_sites`
- `cif`
- `energy_above_hull`

The `energy_above_hull` field is interpreted as eV atom^-1. Binary stability is
defined source-natively as `energy_above_hull <= 0`.

## Materials Project source

Materials Project records were queried on 2026-05-20 through the Materials
Project API. The relevant endpoint was:

```text
MPRester.materials.summary.search
```

The queried fields used for this audit were:

- `material_id`
- `formula_pretty`
- `energy_above_hull`
- `structure`

The Materials Project `energy_above_hull` field is interpreted as eV atom^-1.
Binary stability is defined source-natively as `energy_above_hull <= 0`.

## Official Alexandria-PBE source

The official Alexandria-PBE extension uses the complete PBE 3D database from
the Alexandria Materials Database, snapshot `2025.07.02`:

```text
https://alexandria.icams.rub.de/data/pbe/2025.07.02/
```

The archive was retrieved on 2026-07-05. The analysis uses the complete PBE 3D
JSON shards rather than the convex-hull-only download, because binary
stable/unstable labels require hull values for all matched structures, not only
known hull vertices.

The parsed snapshot contains:

```text
58 JSON bzip2 shards
5,777,914 total records
5,777,914 records with formula, structure and entries[].data.e_above_hull
```

Relevant fields include:

- `entry_id`
- `composition`
- `structure`
- `entries[].data.e_above_hull`
- `entries[].data.prototype_id`
- `entries[].data.run_timestamp`

The `entries[].data.e_above_hull` field is interpreted as eV atom^-1. Binary
stability is defined source-natively as `e_above_hull <= 0`.

Official Alexandria-PBE is audited as a separate source from MatterGen
alex-mp-20. The public outputs therefore distinguish:

- Materials Project;
- MatterGen alex-mp-20;
- official Alexandria-PBE.

## JARVIS-DFT source for secondary extension

The secondary multi-source extension uses JARVIS-DFT records exposed through
the JARVIS OPTIMADE `jarvisdft` structures endpoint:

```text
https://jarvis.nist.gov/optimade/jarvisdft/v1/structures
```

The archived retrieval queried the JARVIS OPTIMADE endpoint on 2026-07-04,
using bucket filters from 1 to 260 and stopping after a 20-bucket empty tail.
The bucket filter is recorded only as retrieval bookkeeping. Scientific fields
are taken from the parsed structure records.

The extension retains records with:

- `dft_3d_` identifiers;
- lattice vectors;
- species at sites;
- Cartesian site positions;
- `_jarvis_ehull`.

The cached retrieval contains 79,637 raw OPTIMADE records and 75,993 usable
JARVIS-DFT 3D records with structures and hull values. The `_jarvis_ehull`
field is interpreted as eV atom^-1. Binary stability is defined source-natively
as `_jarvis_ehull <= 0`.

## Matching denominator

The primary denominator is the retained strict MP-identifier
structure-matched overlap:

```text
43,139 strict MP--alex-mp-20 matches
```

This denominator is derived from 43,984 MatterGen alex-mp-20 rows carrying
Materials Project identifiers. Of these, 43,169 Materials Project records were
retrieved in the archived query and 43,139 passed strict `pymatgen`
`StructureMatcher` matching. The unmatched records and structure mismatches are
audited separately rather than silently discarded.

The JARVIS extension starts from this same 43,139-row denominator. Reduced
formula is used only as a prefilter. Reported JARVIS denominators require exact
`StructureMatcher` matches. The default setting yields 36,544 JARVIS exact match
rows covering 28,273 MP--alex-mp-20 denominator rows. Pairwise source-conflict
rates use the 23,300 rows with exactly one JARVIS exact match. The 4,973 rows
with multiple JARVIS exact matches are reported as a duplicate-match boundary.

The official Alexandria-PBE extension also starts from the 43,139-row
MP--alex-mp-20 denominator. Reduced formula is used only as a prefilter. MP
identifiers are not used to join official Alexandria-PBE rows. Exact matches
are identified with `pymatgen` `StructureMatcher` after formula prefiltering.
The extension yields:

```text
42,818 MP--alex-mp-20 denominator rows with at least one official
  Alexandria-PBE formula candidate
48,755 official Alexandria-PBE exact-match rows
41,760 unique MP--alex-mp-20 denominator rows with at least one exact match
36,802 single-match MP--alex-mp-20--official Alexandria-PBE rows
4,958 rows with multiple official Alexandria-PBE exact matches
```

The single-match denominator is the primary official Alexandria-PBE analysis
set. Multiple-match rows are reported as a duplicate-match boundary and are
included only in deterministic tie-breaking sensitivity analyses.

## Released materials

Raw upstream structure caches and reconstruction inputs remain with their
respective providers. This repository and its archival release provide derived
tables, figure inputs, scripts, tests and SHA256 manifests.

Released derived outputs include:

- matched identifiers and source-native labels;
- source-native hull values used for binary labels;
- match-status counts and excluded-record audits;
- alternative cutoff sensitivity tables;
- chemistry-stratified source-conflict summaries;
- conflict-excluded metric summaries;
- manuscript figure source data;
- JARVIS multi-source denominator flow, exact-match, cutoff-sensitivity and
  three-source label-composition outputs;
- official Alexandria-PBE denominator flow, schema audit, exact-match,
  cutoff-sensitivity, directionality, three-source label-composition,
  alex-mp-20--official Alexandria-PBE hull-value difference, chemistry
  bootstrap and fixed-ranking uncertainty outputs;
- integrity tests and file checksums.

## Interpretation

The released benchmark compares source-native stability endpoints on retained
strict structure-matched cohorts. Common-pool, consensus and audit views are
defined evaluation views, with their construction status recorded in the source
cards. Formula support is used for matching coverage; exact structure matches
define the evaluation denominators. MatterGen alex-mp-20 and official
Alexandria-PBE remain distinct sources throughout the release.
