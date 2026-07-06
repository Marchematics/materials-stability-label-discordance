# SourceAware-Stability Phase 2 outputs

Phase 2 builds a full model-facing and candidate-consequence layer on top of the frozen `outputs/phase1_v2/` benchmark layer. It evaluates how source-aware stability label views change model metrics, rankings, top-K discovery-yield estimates and public-source-aware candidate conclusions.

## Scope guardrail

These outputs are **not homogeneous DFT validation** and do **not** provide physical-truth stability labels. Source-native, common-pool, source-union, consensus, uncertain and audit-view labels remain separate benchmark views. Formula-only overlaps and unmapped Matbench/WBM predictions are provenance/coverage evidence only.

## Primary regeneration command

```bash
python -m sourceaware.phase2.cli build-all \
  --phase1 outputs/phase1_v2 \
  --out outputs/phase2_v1 \
  --external-cache /home/waas/paper_experiments/phase2_external

python -m sourceaware.phase2.cli check --phase1 outputs/phase1_v2 --out outputs/phase2_v1
pytest -q
```

## Main artifact groups

- `model_scores/`: SourceAware-scored model/baseline matrix plus audited external Matbench/WBM artifacts.
- `denominators/`: D5 full-complete, family-complete, pairwise-complete and per-model max-coverage denominators.
- `model_metrics/`: model × label-view metrics, top-K tables, bootstrap intervals, uncertainty/spread ratios and rank correlations.
- `rank_inversions/`: aggregate, pairwise-complete, family, budget and real-model rank-change audits.
- `generative/`: public-source-aware screened/generated candidate consequence, with unmatched/formula-only cases and redacted private/local raw-generation provenance kept separate.
- `leaderboard/`: SourceAware leaderboard alpha and one model card per inventory row.
- `figure_source_data/` and `figures/`: source tables plus SVG/PDF artifacts for Figures 1–6.

## Manuscript safety artifacts

- `phase2_acceptance_check.md/json`: machine-readable pass/guardrail check.
- `phase2_requirement_audit.md/csv`: requirement-by-requirement artifact audit.
- `phase2_claim_support_matrix.md/csv/json`: safe claim language and overclaim guardrails.
- `phase2_key_findings.md/csv/json`: quantitative findings supported by the regenerated outputs.
- `manifest_phase2_v1.json`: SHA256 hashes, file sizes, and table row/column counts.
