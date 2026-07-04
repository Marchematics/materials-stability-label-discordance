# Related Work Positioning Addendum

This addendum supplies manuscript-ready related-work positioning for the
materials stability label source-conflict paper. It adds citation context only.
It does not add experiments, change denominators, or promote any diagnostic row
into a completed model benchmark.

## Why This Addendum Exists

The completed evidence supports the paper's main scientific line: the strict
MP--alex-mp-20 exact-match denominator contains 43,139 structure matches, with
5,060 source-conflicting binary labels and an overall source-conflict burden of
0.1173. The burden remains material under small positive binary stability
cutoffs, MP-source threshold flags capture most conflicts at substantial
annotation burden, and the completed benchmark card turns these facts into a
reporting protocol. The remaining task is literature positioning within
materials benchmarking, foundation machine-learning interatomic potentials
(MLIPs), stable materials prediction, generative materials design, and benchmark
reliability.

## Citation Roles

| Citation key | Manuscript role | Claim supported | Boundary |
|---|---|---|---|
| `choudhary2024jarvis_leaderboard` | Broad benchmark context | Materials AI increasingly values community-comparable, reproducible benchmark infrastructure. | Does not imply this paper is a new leaderboard. |
| `riebesell2025matbench_discovery` | Direct benchmark anchor | Matbench Discovery frames crystal-stability prediction as ML pre-screening for DFT-based stable-materials discovery. | This paper audits label-source uncertainty rather than proposing a stronger model. |
| `batatia2025foundation_mace` | Foundation-MLIP context | MACE-MP represents the foundation-potential model family used in current atomistic modeling. | Use the JCP version instead of the older arXiv citation. |
| `deng2025systematic_softening` | Model-side reliability contrast | Universal MLIPs can have systematic model-side errors, especially in high-energy or OOD regimes. | Distinct from this paper's source-native label uncertainty. |
| `kuner2025mp_aloe` | Data-side reliability context | High-fidelity r2SCAN and off-equilibrium datasets address model-training-data quality. | Future-work context, not a new training-data experiment here. |
| `lysogorskiy2026grace` | Newer foundation-MLIP context | Later MLIP work reports Matbench Discovery performance, showing benchmark uptake by frontier models. | Do not add GRACE as an experiment in this paper. |
| `zou2025thermodynamic_stability` | Stability-prediction application context | Binary thermodynamic stability labels matter beyond structure-to-energy leaderboards. | Background only; not used as an evaluation source. |
| `zeni2025mattergen` | Generative design context | Generative materials models make DFT-derived stability labels central to candidate interpretation. | MatterGen is a provenance context for alex-mp-20, not a new model comparator. |

## Introduction Insertion

Materials-informatics benchmarks have increasingly shifted from reporting isolated prediction errors to evaluating reproducible model utility in discovery workflows. JARVIS-Leaderboard provides a broad community benchmark infrastructure across materials-design tasks, while Matbench Discovery focuses specifically on machine-learning models as pre-screeners for DFT-based stable-crystal discovery. In parallel, foundation interatomic potentials and generative materials models have made DFT-derived stability labels central to both screening and design. These developments make the reliability of the binary stability endpoint itself a benchmark question: if the same matched structure receives different stable/unstable labels across public DFT sources, leaderboard scores and generated-candidate claims inherit a source-label uncertainty that is not visible from a single-source benchmark alone.

## Related Work Paragraph

This work is closest to materials benchmark studies, but it asks a different question from model ranking. JARVIS-Leaderboard emphasizes reproducible, community-comparable evaluation across materials-design tasks, and Matbench Discovery sharpens this idea for crystal-stability prediction by treating ML models as pre-filters for high-throughput DFT discovery. Recent foundation MLIPs such as MACE and GRACE, together with charge-informed and message-passing potentials used in Matbench-style evaluations, have made these benchmarks a shared language for comparing models. Our contribution is orthogonal to proposing another model or completing another leaderboard row. We audit whether the binary DFT stability labels used by such benchmarks are source-invariant for the same exactly matched structures, and we provide source-label uncertainty tables that can accompany benchmark reports.

## Discussion Insertion

Our analysis is complementary to recent work on model-side and data-side reliability of universal MLIPs. Systematic softening studies diagnose how pretrained potentials can distort high-energy or out-of-distribution regions of the potential-energy surface, while high-fidelity datasets such as MP-ALOE aim to improve coverage of off-equilibrium configurations and functional fidelity. By contrast, the present study holds public source-native labels fixed and asks whether the binary stability endpoint changes across DFT databases for the same matched structure. These are distinct uncertainty channels: model-side error, training-data provenance, source-native hull construction and binary-threshold sensitivity should be reported separately rather than collapsed into a single benchmark score.

## Stable Prediction And Generation Context

Binary DFT stability labels also shape composition-based stability prediction and generative inorganic-materials design. Composition-only and ensemble models use stability labels as learning targets for broad thermodynamic screening, while MatterGen-style generative models use stability as a central criterion for interpreting generated crystals. This makes source-dependent label uncertainty relevant beyond a single leaderboard: it affects how predicted or generated candidates are described, filtered and compared before any experimental synthesis claim can be made.

## Future Work Sentence

Future work should combine full-denominator label-source audits with full-denominator scoring of newer foundation MLIPs such as GRACE or other cross-domain potentials where public, reproducible predictions are available on the same exact-match denominator. That extension is outside the scope of the present source-label reproducibility study.

## Scope Guardrails

- Do not claim a new GRACE, SevenNet, MatterSim, Orb or MatterGen experiment.
- Do not claim a complete Matbench Discovery leaderboard audit.
- Do not claim external DFT databases are interchangeable ground truth.
- Do not claim source-wide burden outside the retained MP--alex-mp-20
  denominator.
- Do not claim a common-hull or physical-correctness adjudication.

## Allowed Replacement Language

- "This paper audits label-source uncertainty in stability benchmarks."
- "The full MP--alex-mp-20 denominator shows modest but nonzero source-conflict burden concentrated near the stability threshold."
- "The result is complementary to model-side MLIP error analyses and data-side high-fidelity training-set construction."
- "Newer foundation MLIPs motivate the benchmark-reliability question, but they are not evaluated as new experimental rows here."

## Source Notes

The citation metadata in `docs/bibliography_additions.bib` was checked against publisher or institutional pages where available. JARVIS-Leaderboard is npj Computational Materials 10, article 93 (2024). Matbench Discovery is Nature Machine Intelligence 7, 836-847 (2025). The MACE foundation-model citation should use the Journal of Chemical Physics article 163, 184110 (2025), not only the earlier arXiv version. MatterGen is Nature 639, 624-632 (2025). GRACE is npj Computational Materials 12, article 114 (2026).
