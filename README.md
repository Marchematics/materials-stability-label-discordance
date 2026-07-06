# Source-aware convex-hull benchmark framework

**Phase 1 release: reusable source-aware benchmark layer, not a full homogeneous-DFT referee benchmark.**

**Phase 2 working layer:** `outputs/phase2_v1/` extends the frozen Phase 1
benchmark into model-facing and screened-candidate consequence diagnostics:
model-score inventory, D5-style model denominators, model × label-view metrics,
top-K stable-yield/uncertainty tables, rank-inversion audits, a SourceAware
leaderboard alpha, figure source data and an explicit candidate-consequence
scope audit. Phase 2 remains a public-source-aware benchmark evaluation layer;
it is **not** homogeneous DFT validation and does **not** assert physical-truth
stability labels.

A reproducibility-focused toolkit for **source-native stability-label audits**,
**common-pool convex-hull relabeling**, **source-aware benchmark datasets** and
**model/candidate consequence diagnostics** in machine-learning
crystal-discovery benchmarks. The repository supports the public data/code and
figure artifacts for the study:

```text
A source-aware convex-hull framework for reliable AI crystal-discovery
benchmarks
```

Machine-learning crystal discovery often treats binary DFT-derived stability
labels as interchangeable across public databases. This repository audits that
assumption across Materials Project, MatterGen alex-mp-20 and official
Alexandria-PBE source-native labels, then reconstructs a matched common phase
pool where source-comparable formation energies are available.

Headline result: on 43,139 strict MP--alex-mp-20 structure matches, 5,060
(11.7%) carry source-conflicting binary stability labels; the burden persists
under metastability-tolerant cutoffs (11.45% at 5 meV atom^-1 and 9.02% at
25 meV atom^-1) and is chemically nonuniform.

Official Alexandria-PBE extension: the complete official Alexandria-PBE 3D
database snapshot `2025.07.02` contains 5,777,914 usable records with
`entries[].data.e_above_hull`, `entries[].data.e_form`, formula and structure fields. Exact
formula-prefiltered structure matching yields a 36,802-row single-match
MP--alex-mp-20--official Alexandria-PBE denominator. On these same structures,
exact-zero source-conflict burdens are 15.4% for MP--official Alexandria-PBE,
10.5% for MatterGen alex-mp-20--official Alexandria-PBE and 11.5% for
MP--MatterGen alex-mp-20.

Common-pool reconstruction: for the MP--official Alexandria-PBE pair, source-
comparable formation energies allow a matched-denominator common-pool hull for
36,770/36,802 single-match triple-denominator rows. The MP--official
Alexandria-PBE conflict rate decreases from 15.4% under source-native public
labels to 13.3% under the common phase pool. The common pool removes 3,659
native conflicts and leaves 2,002 persistent source-energy/workflow conflicts;
the remaining 5 native conflicts are unreconstructable. A broader available
exact-match source-union sensitivity gives a 13.9% common-pool conflict rate,
showing that the phase-pool-sensitive and residual source-energy/workflow
components are not artifacts of the matched-denominator pool definition.
As a threshold overlay, 4,502/5,666 source-native MP--official Alexandria-PBE
conflicts and 3,252/4,897 common-pool conflicts have crossing margins at or
below 25 meV atom^-1.
MatterGen alex-mp-20 is marked unreconstructable in this layer because the
public-safe inputs do not include source-comparable formation energies.

Source-aware relabeling benchmark-change diagnostic: under each source's own
public-hull ranking, the source-native top-K list is 100% stable by
construction for that source. Requiring stability in all three source-native
labels and in both reconstructable MP--official Alexandria-PBE common-pool
labels lowers the apparent stable fraction to 68.0%, 74.0% and 88.0% for the
MP, MatterGen alex-mp-20 and official Alexandria-PBE top-100 lists,
respectively. At K=5000, the corresponding source-aware consensus fractions
are 62.2%, 67.7% and 74.6%.

Model-facing consequence analysis: four full-coverage model score sources
(`CHGNet`, `MACE-MP`, `M3GNet` and `ALIGNN-FF`) were scored on the
SourceAware-Stability-36K denominator and evaluated under source-native,
common-pool, consensus, conflict-excluded and uncertain-excluded label views.
The released outputs report label-view metric bands, rank correlations and
rank-inversion counts. Raw model energies are used as diagnostic rankings, not
as calibrated formation-energy or hull predictors.

Screened-candidate consequence analysis: no public generated-candidate table
from MatterGen, CDVAE, DiffCSP, FlowMM or CrystalFlow was found in this
repository. The available CHGNet 5k screened-candidate table is therefore used
as a screened-candidate consequence analysis only. Among 4,291 matched rows,
the declared source-native stable rate is 40.6%, the consensus-stable rate is
26.0%, and the drop from source-native stable claims to consensus-stable claims
is 36.1%.

Benchmark product: `SourceAware-Stability-36K` is released as a public-safe
36,802-row benchmark table with source-native labels, common-pool labels,
consensus/uncertain states, threshold-sensitivity flags and deterministic
chemical-system grouped train/validation/test splits.

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
| Source-aware benchmark dataset | `outputs/SourceAware-Stability-36K/` |
| Model leaderboard-impact diagnostics | `outputs/milestones/model_leaderboard_impact/` |
| Source-union common-pool sensitivity | `outputs/milestones/source_union_common_pool/` |
| Screened-candidate consequence analysis | `outputs/milestones/generated_candidate_impact/` |
| Homogeneous DFT spot-check selection | `outputs/milestones/homogeneous_dft_spotcheck/` |
| Transition figure data | `outputs/figures/source_native_to_common_pool_transition.*` |
| Benchmark card and protocol | `outputs/milestones/benchmark_reliability_enhancement/table_source_aware_benchmark_card.csv`; template: `templates/BENCHMARK_CARD_TEMPLATE.md` when present |
| Data provenance | `DATA_PROVENANCE.md` |
| Integrity tests | `tests/` |

Key scripts:

- `build_phase2_v1.py` builds the Phase 2 model-facing and candidate-consequence
  layer from frozen `outputs/phase1_v2/` inputs.
- `run_full_mp_alex_denominator_43984.py` builds the 43,139-row source-linked denominator.
- `run_structure_matching_tolerance_sweep.py` checks denominator sensitivity to `StructureMatcher` tolerances.
- `build_benchmark_reliability_enhancement.py` builds benchmark-card, cutoff, threshold and chemistry diagnostics.
- `build_m2_cluster_robust_chemistry.py` builds chemistry-stratified cluster-bootstrap intervals.
- `build_benchmark_impact_label_source_choice.py` builds label-transfer and conflict-excluded sensitivity tables.
- `build_common_hull_mechanism_subset.py` and `analyze_formation_energy_mechanism.py` build mechanism-boundary diagnostics.
- `build_common_pool_convex_hull_layer.py` builds matched-denominator
  common-pool hull labels, conflict decomposition and conservative consensus
  labels for the MP--official Alexandria-PBE reconstructable pair.
- `build_source_union_common_pool_hulls.py` builds the available exact-match
  source-union common-pool sensitivity layer.
- `build_source_native_to_common_pool_transition.py` builds the exact
  transition-accounting figure inputs.
- `build_sourceaware_stability_benchmark.py` builds the
  `SourceAware-Stability-36K` dataset product and splits.
- `score_sourceaware_stability_models.py` scores CHGNet, MACE-MP, M3GNet and
  ALIGNN-FF raw model-energy rankings on the source-aware denominator.
- `evaluate_model_leaderboard_under_source_aware_labels.py` evaluates model
  rankings under source-native, common-pool, consensus and exclusion label
  views.
- `evaluate_generated_candidate_stability_claims.py` evaluates generated or,
  when generated sets are unavailable, screened-candidate stable-yield
  sensitivity under source-aware labels.
- `select_homogeneous_dft_spotcheck_set.py` exports a ready-to-run homogeneous
  DFT validation selection set without claiming validation results.
- `build_source_aware_relabeling_benchmark_change.py` quantifies how fixed
  public-hull top-K conclusions change after source-aware consensus relabeling.
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
- Matched-denominator common-pool hull reconstruction is available for
  36,770/36,802 MP--official Alexandria-PBE rows. It lowers the pairwise
  conflict fraction from 15.4% to 13.3%, assigns 3,659 native conflicts to a
  phase-pool-sensitive component, leaves 2,002 persistent source-energy/workflow
  conflicts, has 5 unreconstructable native conflicts and defines 9,487 strict
  source-aware consensus-stable rows in `SourceAware-Stability-36K`. The
  threshold overlay reports 4,502/5,666 source-native conflicts and
  3,252/4,897 common-pool conflicts within a 25 meV atom^-1 crossing margin.
- The available exact-match source-union common-pool sensitivity has a 13.9%
  conflict fraction, resolves 3,401/5,666 native conflicts and leaves a 39.9%
  persistent residual fraction. It is not a full MP-wide or Alexandria-wide
  source-union hull.
- The source-native to common-pool transition accounting closes exactly:
  5,666 = 3,659 phase-pool-sensitive + 2,002 persistent source-energy/workflow
  + 5 unreconstructable native conflicts. A further 2,895 source-native
  concordant rows become hidden common-pool conflicts.
- Source-aware relabeling changes fixed public-hull benchmark conclusions:
  source-native top-K lists are 100% stable under the ranking source by
  construction, but three-source plus common-pool consensus stable fractions
  fall to 68.0--88.0% at K=100 and 62.2--74.6% at K=5000, depending on the
  ranking source.
- Four full-coverage model score sources are evaluated under nine label views.
  The model-facing outputs report label-source uncertainty bands and rank
  inversions; claims are restricted to diagnostic model rankings from raw model
  energy scores.
- A screened-candidate consequence analysis finds that source-aware relabeling
  reduces the stable-yield interpretation of the matched CHGNet 5k screened
  candidate table from 40.6% source-native stable to 26.0% consensus stable.
- A 48-structure homogeneous DFT spot-check selection set is provided as a
  ready-to-run validation set; no homogeneous DFT result is claimed here.

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
(cd outputs/milestones/official_alexandria_pbe_extension && sha256sum -c MANIFEST_SHA256.txt)
python scripts/build_common_pool_convex_hull_layer.py
(cd outputs/milestones/common_pool_convex_hull_layer && sha256sum -c MANIFEST_SHA256.txt)
python scripts/build_source_aware_relabeling_benchmark_change.py
(cd outputs/milestones/source_aware_relabeling_benchmark_change && sha256sum -c MANIFEST_SHA256.txt)
python scripts/build_sourceaware_stability_benchmark.py
(cd outputs/SourceAware-Stability-36K && sha256sum -c SHA256SUMS.txt)
python scripts/evaluate_model_leaderboard_under_source_aware_labels.py
python scripts/build_source_union_common_pool_hulls.py
(cd outputs/milestones/source_union_common_pool && sha256sum -c MANIFEST_SHA256.txt)
python scripts/evaluate_generated_candidate_stability_claims.py
(cd outputs/milestones/generated_candidate_impact && sha256sum -c MANIFEST_SHA256.txt)
python scripts/select_homogeneous_dft_spotcheck_set.py
(cd outputs/milestones/homogeneous_dft_spotcheck && sha256sum -c MANIFEST_SHA256.txt)
python scripts/build_source_native_to_common_pool_transition.py
(cd outputs/figures && sha256sum -c MANIFEST_SHA256.txt)
```

Raw upstream archives and Materials Project structure caches are not
redistributed. The repository contains public-safe derived tables, figure
inputs, scripts, tests and manifests.

## Reporting Checklist

A source-aware binary stability benchmark report should include:

- label database, version, field name, units and query date;
- structure-matching rule and retained denominator;
- missing identifiers and structure mismatches;
- source-conflict burden and directionality;
- common-pool reconstruction status where formation energies are available;
- source-union sensitivity or an explicit coverage/failure report;
- threshold overlays on source-native and reconstructed conflicts;
- conservative consensus labels when a common pool can be reconstructed;
- benchmark, model-ranking and candidate-yield summaries before and after
  source-aware relabeling;
- alternative cutoffs such as 5 and 25 meV atom^-1;
- a non-tautological near-threshold flag and its annotation burden;
- conflict-excluded metrics;
- public-safe identifiers, labels, hull values, scripts and checksums.

## Data and Code Availability

A static, citable snapshot of the public-safe data and code is archived at
Zenodo: https://doi.org/10.5281/zenodo.20392665. This repository is the public
development repository. The framework release is identified as
`v1.4-sourceaware-reliability-framework`.

## License

Code in this repository is released under the [MIT License](LICENSE). Derived
data artifacts archived at Zenodo are released under CC BY 4.0.
