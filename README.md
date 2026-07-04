# Source-aware MP--alex-mp-20 stability benchmark

A reproducibility-focused audit toolkit for **source-native stability labels**
in machine-learning crystal-discovery benchmarks. The repository supports the
public data/code and figure artifacts for the study:

```text
Source-aware reporting for Materials Project and MatterGen alex-mp-20
stability labels in crystal-discovery benchmarks
```

Machine-learning crystal discovery often treats binary DFT-derived stability
labels as interchangeable across public databases. This repository audits that
assumption on a strict MP-identifier structure-matched denominator comparing
Materials Project labels with MatterGen alex-mp-20 labels.

Headline result: on 43,139 strict MP--alex-mp-20 structure matches, 5,060
(11.7%) carry source-conflicting binary stability labels; the burden persists
under metastability-tolerant cutoffs (11.45% at 5 meV atom^-1 and 9.02% at
25 meV atom^-1) and is chemically nonuniform.

## Data Source Naming

The second label source is **MatterGen alex-mp-20**, not an unmodified
Alexandria label table. The local data source is the MatterGen data-release
archive `alex_mp_20.zip`; its README describes `alex-mp` as the Alex-MP dataset
used to train and fine-tune MatterGen. The release contains structures from
Alexandria and MP-20 and reports an `energy_above_hull` field after the
MatterGen data-release filtering and relaxation workflow.

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

## Primary Public Results

- 43,984 unique MatterGen alex-mp-20 rows carry Materials Project identifiers.
- 43,169 corresponding Materials Project records were retrieved in the archived query.
- 43,139 rows pass strict `pymatgen` `StructureMatcher` matching and define the primary MP--alex-mp-20 denominator.
- 5,060 / 43,139 matched structures have source-conflicting binary stability labels, giving an 11.7% source-conflict burden.
- The burden remains material under positive stability cutoffs: 11.45% at 5 meV atom^-1 and 9.02% at 25 meV atom^-1.
- An MP-source 5 meV atom^-1 threshold flag captures 82.4% of conflicts while flagging 45.8% of the denominator.

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

Run repository-level tests:

```bash
pytest -q tests
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
development repository.

## License

Code in this repository is released under the [MIT License](LICENSE). Derived
data artifacts archived at Zenodo are released under CC BY 4.0.
