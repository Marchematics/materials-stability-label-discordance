# Source-Aware Stability-Benchmark Card (blank template)

A reusable reporting template for any binary DFT-derived stability benchmark in
which two or more public source-native labels are available for the same
matched structures (e.g. Materials Project, Alexandria, OQMD, JARVIS, AFLOW).
Copy this file, fill every field, and ship it alongside your benchmark result.

See `outputs/milestones/benchmark_reliability_enhancement/table_source_aware_benchmark_card.csv`
for a completed instantiation on the MP–Alexandria denominator.

---

## 1. Label source

- **Source A:** <database, version/snapshot, label field, e.g. MP `energy_above_hull`>
- **Source B:** <database, version/snapshot, label field>
- **Stability threshold:** <e.g. source-native e_above_hull ≤ 0 eV/atom>
- **Hull reference convention:** <each source's own hull / shared hull / other>

## 2. Denominator construction

- **Matching method:** <e.g. pymatgen StructureMatcher; ltol, stol, angle_tol>
- **Candidate universe:** <how rows were selected; identifier join or formula>
- **Matched denominator N:** <count>
- **Excluded / unmatched:** <count and reason: missing records, mismatches>
- **Scope statement:** <source-linked overlap? random intersection? census?>

## 3. Source-conflict burden

- **Discordant labels n / N:** <count> / <N> = <fraction>
- **Uncertainty interval:** <method, e.g. chemistry-cluster bootstrap 95% CI>
- **Directionality:** <A-stable/B-unstable vs B-stable/A-unstable counts>
- **Agreement-only retained fraction:** <fraction>

## 4. Near-threshold sensitivity

- **Alternative binary cutoffs:** <discordance at e.g. 5, 10, 25 meV/atom>
- **Near-hull flag threshold:** <threshold>
- **Flag burden:** <flagged / N>
- **Conflict recall of the flag:** <captured discordant / total discordant>

## 5. Conflict-excluded performance

- **Conflict-excluded denominator:** <fraction retained after dropping conflicts>
- **Model read-out sensitivity:** <metric shift between source-A and source-B labels,
  e.g. precision@K, AUROC, ranking flip yes/no>

## 6. Reproducibility outputs

- **Data:** <matched table, source data, file list, SHA256 manifest>
- **Code:** <scripts / repository / archive DOI>
- **Restricted inputs:** <raw caches or exports not redistributed, if any>

---

### Recommended reporting statement

> Disclose label source, hull convention, source-conflict burden,
> near-threshold burden and conflict-excluded sensitivity metrics alongside any
> binary stability endpoint. Source-native public labels are usable, but they
> are not interchangeable benchmark ground truth; source dependence must be
> stated.
