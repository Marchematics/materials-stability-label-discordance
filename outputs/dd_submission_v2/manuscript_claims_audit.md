# Manuscript claims audit

Status: **PASS**

Evidence scope: frozen `outputs/phase1_v2` and `outputs/phase2_v1` only. NMI/referee scaffolds are excluded.

## Denominators

- F0: 34,962 — formula-support catalogue
- D1: 43,139 — MP--alex-mp-20 exact
- D2: 36,802 — three-source single-match exact
- D4: 36,802 — source-union target/status
- D5: 36,801 — four-real-model complete

## Conflict identities

- reconstructable_native: 5,661 = phase_pool_sensitive 3,659 + persistent 2,002
- common_pool_conflicts: 4,897 = persistent 2,002 + hidden_common_pool 2,895
- native_full: 5,666 = reconstructable_native 5,661 + unreconstructable 5

## Source-native endpoint switches

- MP vs official Alexandria-PBE: 5,666/36,802 = 15.40%
- alex-mp-20 vs official Alexandria-PBE: 3,862/36,802 = 10.49%
- MP vs alex-mp-20: 4,244/36,802 = 11.53%
- MP vs alex-mp-20 (strict full): 5,060/43,139 = 11.73%

## Model evidence boundary

- Primary exact models: ALIGNN-FF, CHGNet, M3GNet, MACE-MP (4 models; D5 n=36,801).
- All other model entries are external WBM context, artifact inventory, baselines or oracle diagnostics.
- Scores are diagnostic rankings, not calibrated source-comparable hull distances.
- Full-denominator classification-metric top-model inversion rows: 0.
- Legacy lower-rank audit rows (all three model denominators and all metric families): 216.
- Aggregate diagnostic winner flips: 10,468/77,616 = 13.49% (includes baselines/oracles).
- Real-model-only winner flips: 377/7,056 = 5.34%.

## Guardrails

- No homogeneous DFT referee truth labels.
- No generated-material validation.
- No complete full-source-union hull claim.
- Consensus, common-pool, source-union and audit labels are benchmark diagnostics, not physical truth.
