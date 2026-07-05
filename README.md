# Multi-source stability-label provenance benchmark

A reproducibility-focused audit toolkit for **source-native stability labels**
in machine-learning crystal-discovery benchmarks. The repository supports the
public data/code and figure artifacts for the study:

```text
Source-native stability labels are not source-invariant in multi-source
crystal-discovery benchmarks
```

Machine-learning crystal discovery often treats binary DFT-derived stability
labels as interchangeable across public databases. This repository audits that
assumption across Materials Project, MatterGen alex-mp-20 and official
Alexandria-PBE source-native labels.

Headline result: on 43,139 strict MP--alex-mp-20 structure matches, 5,060
(11.7%) carry source-conflicting binary stability labels; the burden persists
under metastability-tolerant cutoffs (11.45% at 5 meV atom^-1 and 9.02% at
25 meV atom^-1) and is chemically nonuniform.

Official Alexandria-PBE extension: the complete official Alexandria-PBE 3D
database snapshot `2025.07.02` contains 5,777,914 usable records with
`entries[].data.e_above_hull`, formula and structure fields. Exact
formula-prefiltered structure matching yields a 36,802-row single-match
MP--alex-mp-20--official Alexandria-PBE denominator. On these same structures,
exact-zero source-conflict burdens are 15.4% for MP--official Alexandria-PBE,
10.5% for MatterGen alex-mp-20--official Alexandria-PBE and 11.5% for
MP--MatterGen alex-mp-20.

Additional JARVIS-DFT extension: JARVIS-DFT 3D records queried on 2026-07-04
through the JARVIS OPTIMADE endpoint were exact-matched to the archived
MP--alex-mp-20 denominator. The extension retains 23,300 single-match
MP--alex-mp-20--JARVIS rows for pairwise source-conflict rates. It is a
source-native public-label audit only; it does not use formula-only matches and
does not reconstruct a common hull.

## Data Source Naming

The second label source is **MatterGen alex-mp-20**, not an unmodified
Alexandria label table. The local data source is the MatterGen data-release
archive `alex_mp_20.zip`; its README describes `alex-mp` as the Alex-MP dataset
used to train and fine-tune MatterGen. The release contains structures from
Alexandria and MP-20 and reports an `energy_above_hull` field after the
MatterGen data-release filtering and relaxation workflow.

The third primary source is **official Alexandria-PBE**, retrieved from the
official Alexandria Materials Database complete PBE 3D JSON snapshot
`2025.07.02`. It is audited separately from MatterGen alex-mp-20 and is never
used as a synonym for alex-mp-20.

## Repository Layout

| Module | Location |
|---|---|
| Public manuscript figures | `manuscript/figures/` |
| Analysis scripts | `scripts/` |
| Public-safe data and manifests | `outputs/milestones/` |
| Benchmark card and protocol | `outputs/milestones/benchmark_reliability_enhancement/table_source_aware_benchmark_card.csv`; template: `templates/BENCHMARK_CARD_TEMPLATE.md` when present |
| Data provenance | `DATA_PROVENANCE.md` |
| Integrity tests | `tests/` |

Key scripts:

- `run_full_mp_alex_denominator_43984.py` builds the 43,139-row source-linked denominator.
- `run_structure_matching_tolerance_sweep.py` checks denominator sensitivity to `StructureMatcher` tolerances.
- `build_benchmark_reliability_enhancement.py` builds benchmark-card, cutoff, threshold and chemistry diagnostics.
- `build_m2_cluster_robust_chemistry.py` builds chemistry-stratified cluster-bootstrap intervals.
- `build_benchmark_impact_label_source_choice.py` builds label-transfer and conflict-excluded sensitivity tables.
- `build_common_hull_mechanism_subset.py` and `analyze_formation_energy_mechanism.py` build mechanism-boundary diagnostics.
- `build_manuscript_figures.py` builds public manuscript Fig. 1--4.
- `build_official_alexandria_pbe_feasibility.py` validates the official
  Alexandria-PBE complete 3D snapshot, checks `e_above_hull` coverage and
  builds the exact-structure overlap denominator.
- `build_official_alexandria_pbe_extension_outputs.py` builds official
  Alexandria-PBE cutoff, directionality, label-composition, hull-value
  difference, chemistry-bootstrap and fixed-ranking uncertainty tables.
- `build_jarvis_multisource_extension.py` downloads/parses JARVIS OPTIMADE 3D records, exact-matches them to the MP--alex-mp-20 denominator and builds Fig. 5 source tables.

## Primary Public Results

- 43,984 unique MatterGen alex-mp-20 rows carry Materials Project identifiers.
- 43,169 corresponding Materials Project records were retrieved in the archived query.
- 43,139 rows pass strict `pymatgen` `StructureMatcher` matching and define the primary MP--alex-mp-20 denominator.
- 5,060 / 43,139 matched structures have source-conflicting binary stability labels, giving an 11.7% source-conflict burden.
- The burden remains material under positive stability cutoffs: 11.45% at 5 meV atom^-1 and 9.02% at 25 meV atom^-1.
- An MP-source 5 meV atom^-1 threshold flag captures 82.4% of conflicts while flagging 45.8% of the denominator.
- In the secondary JARVIS extension, the single-match triple denominator has 23,300 rows; exact-zero source-conflict burdens are 20.3% for MP--JARVIS, 24.5% for alex-mp-20--JARVIS and 13.0% for MP--alex-mp-20 on that denominator.
- In the official Alexandria-PBE extension, the complete PBE 3D snapshot has
  5,777,914 usable records with `e_above_hull`; the primary single-match
  MP--alex-mp-20--official Alexandria-PBE denominator has 36,802 rows.
- On that official Alexandria-PBE denominator, exact-zero source-conflict
  burdens are 15.4% for MP--official Alexandria-PBE, 10.5% for
  alex-mp-20--official Alexandria-PBE and 11.5% for MP--alex-mp-20.
- Including multiple official Alexandria-PBE exact matches under deterministic
  tie-breaking gives the same qualitative ordering and slightly higher
  MP--official Alexandria-PBE burdens.

These numbers are source-native benchmark diagnostics. They should be reported
with the denominator, matching rule, label field, source version and query date.

## Reproducibility

This repository supports exact reproduction from archived public-safe derived
tables. Rebuilding the denominator from live public records requires Materials
Project API access and is only approximately reproducible because live API
behavior and database contents can change.

Install the Python requirements when using the scripts:

```bash
pip install -r requirements.txt
```

Run repository-level tests and verify milestone manifests:

```bash
pytest -q tests
python scripts/build_official_alexandria_pbe_extension_outputs.py
sha256sum -c outputs/milestones/official_alexandria_pbe_extension/MANIFEST_SHA256.txt
```

Raw Materials Project structure caches and restricted local reconstruction
inputs are not redistributed. Analyses depending on those inputs are archived
as public-safe summaries.

## Reporting Checklist

A source-aware binary stability benchmark report should include:

- label database, version, field name, units and query date;
- structure-matching rule and retained denominator;
- missing identifiers and structure mismatches;
- source-conflict burden and directionality;
- alternative cutoffs such as 5 and 25 meV atom^-1;
- a non-tautological near-threshold flag and its annotation burden;
- conflict-excluded metrics;
- public-safe identifiers, labels, hull values, scripts and checksums.

## Data and Code Availability

A static, citable snapshot of the public-safe data and code is archived at
Zenodo: https://doi.org/10.5281/zenodo.20392665. This repository is the public
development repository. The official Alexandria-PBE extension release is
identified as `v1.2-official-alexandria-extension`.

## License

Code in this repository is released under the [MIT License](LICENSE). Derived
data artifacts archived at Zenodo are released under CC BY 4.0.
