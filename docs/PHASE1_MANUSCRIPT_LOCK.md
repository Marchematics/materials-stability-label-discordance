# Phase 1 manuscript lock: SourceAware-Stability v2 benchmark core

**Release tag target:** `v2.0-phase1-sourceaware-benchmark-core`

**Phase 1 release framing:** reusable source-aware benchmark layer, not a full homogeneous-DFT referee benchmark.

This lock intentionally frames source-native labels, matched common-pool labels, source-union diagnostics, consensus labels and audit views as **benchmark diagnostics**, not physical-truth labels. The public repository does not add manuscript LaTeX, bibliography/style files or PDFs; this document records the Phase 1 manuscript ordering and abstract to keep the text aligned with the released benchmark core.

## Locked abstract draft

Binary DFT-derived stability labels are widely used as benchmark endpoints in AI crystal discovery, but they are tied to a source, phase pool and convex-hull construction. We introduce SourceAware-Stability v2, a reusable source-aware benchmark layer that represents crystal-stability evaluation through explicit denominator hierarchies, source-native labels, common-pool and source-union diagnostics, consensus labels, audit views and automatically generated benchmark cards. Across Materials Project, MatterGen alex-mp-20 and official Alexandria-PBE, the single-match triple denominator contains 36,802 exact-structure rows, and source switching changes 10.5–15.4% of binary endpoints. Common-pool and source-union diagnostics separate phase-pool-sensitive changes from persistent source-energy/workflow components without treating any diagnostic hull as physical truth. On the 36,801-row model-complete denominator, label-view uncertainty propagates into model metrics and top-K stable-yield estimates. We release regenerated denominator tables, label views, figure source data, benchmark-card schema, command-line tools and integrity tests, establishing source-aware label reporting as a required component of reliable crystal-discovery benchmarks.

## Locked Results order

### Result 1: Source-aware labels change benchmark outputs

Lead with Figure 1: label-view metric bands, top-K stable-yield bands and uncertain-fraction burden. Do **not** begin the Results with the denominator story; the first claim is that endpoint choice changes benchmark outputs.

### Result 2: A reusable SourceAware benchmark layer

Introduce the benchmark product itself: D0–D5 denominator hierarchy, source cards, benchmark card, CLI, schema, manifests and integrity tests. Emphasize that the release is a reusable benchmark layer.

### Result 3: Three-source exact denominator and source-native conflict burden

Then present the exact-structure denominators and source-native burden: 43,139 MP–alex-mp-20 strict exact matches; 36,802 MP–alex-mp-20–official Alexandria-PBE single-match rows; and 10.5–15.4% binary endpoint changes under source switching.

### Result 4: Common-pool and source-union diagnostics decompose conflict sources

Present matched common-pool diagnostics and source-union diagnostics as decomposition tools. State the full-source-union caveat explicitly: when full MP/API or complete source phase-pool construction is unavailable, the output is marked incomplete and exact-match source-union compatibility rows are not promoted to full-source-union labels.

### Result 5: Chemistry / near-threshold diagnostics

Retain the chemistry-stratified and near-threshold analyses, but compress them. Their role is to characterize where instability/discordance burden concentrates, not to displace the benchmark-layer framing.

### Result 6: Model-facing benchmark uncertainty

Close with the D5 = 36,801 model-complete denominator, model metrics under multiple label views and top-K stable-yield uncertainty. Use this result as the bridge to Phase 2; do not claim a complete leaderboard replacement or physical-truth adjudication in Phase 1.

## Frozen Phase 1 public artifacts

The Phase 1 release freezes:

- `outputs/phase1_v2/`
- `sourceaware/`
- Phase 1 regeneration scripts in `scripts/`
- Phase 1 integrity tests in `tests/`
- `outputs/phase1_v2/benchmark_card_main.json`
- `outputs/phase1_v2/benchmark_card_main.md`
- `outputs/phase1_v2/manifest_phase1_v2.json`

The release remains scoped as a source-aware benchmark core. It is not a full homogeneous-DFT referee benchmark and does not provide final physical-truth stability labels.
