# Data provenance

This repository audits source-native binary stability labels on a strict
Materials Project--alex-mp-20 MP-identifier structure-matched denominator. It
does not reconstruct a common hull and does not treat either source as absolute
physical truth.

## MatterGen alex-mp-20 source

The second label source is **MatterGen alex-mp-20**, not an unmodified
Alexandria label table. The local source archive is:

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

## Redistribution scope

Raw Materials Project structure caches, restricted local reconstruction inputs
and upstream local validation exports are not redistributed in this repository.
The public repository and Zenodo archive instead provide public-safe derived
tables, figure inputs, scripts, tests and SHA256 manifests.

Public-safe derived outputs include:

- matched identifiers and source-native labels;
- source-native hull values used for binary labels;
- match-status counts and excluded-record audits;
- alternative cutoff sensitivity tables;
- chemistry-stratified source-conflict summaries;
- conflict-excluded metric summaries;
- manuscript figure source data;
- integrity tests and file checksums.

## Scope guardrails

The study reports source-native label dependence. It does not claim:

- a common-hull reconstruction;
- prospective materials discovery;
- independent DFT validation;
- alex-mp-20-wide or database-wide source-conflict prevalence beyond the
  retained MP-identifier structure-matched denominator;
- that MatterGen alex-mp-20 labels are unmodified Alexandria labels.
