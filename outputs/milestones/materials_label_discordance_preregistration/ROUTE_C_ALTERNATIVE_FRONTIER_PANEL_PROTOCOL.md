# Route C: Alternative Frontier Panel Protocol

## Status

```text
protocol_only
no Route C ranking outcomes inspected
Route B remains blocked and unconsumed
```

## Boundary Statement

Because the preregistered ALIGNN-FF scorer was not reproducibly executable, we
define a separate alternative-frontier panel before inspecting any Route-C
ranking outcomes. Route B remains unconsumed and blocked.

Route C is not a continuation of Route B. It is a new preregistered rescue
family with a different model panel, created only after the ALIGNN-FF readiness
gate failed for arbitrary MP-vs-Alex structures.

## Purpose

Route C asks whether the materials-label discordance signal changes downstream
frontier-model conclusions when the primary model panel is restricted to
locally executable or otherwise frozen modern materials models.

It does not claim that ALIGNN-FF was negative, unimportant, or replaceable
inside Route B. ALIGNN-FF remains part of Route B, and Route B remains blocked
until the ALIGNN-FF scorer or frozen same-denominator predictions become
available.

## Candidate Model Panel

Primary Route C panel:

```text
CHGNet
MACE-MP
one of: SevenNet / MatterSim / Orb / MatGL / M3GNet
```

The third model must be chosen before any Route C ranking outcome is computed.
It must have either:

1. frozen public predictions on the exact same MP-vs-Alex denominator; or
2. a locally executable public-weight scorer with recorded package version,
   model identifier, settings, and score-table SHA256.

Fallback panel if no third model is reproducibly available:

```text
CHGNet
MACE-MP
```

The fallback panel may be reported only as a reduced-panel diagnostic. It may
not be described as the full alternative-frontier primary panel.

## Frozen Endpoint

```text
source A: Materials Project API-derived public records
source B: independently downloaded Alexandria / alex-mp snapshot
match rule: strict StructureMatcher high-confidence matches
minimum denominator: n_common >= 200
primary label: stable iff e_above_hull <= 0 eV/atom
primary metric: stable-class F1
co-primary robustness metric: balanced accuracy
threshold: top max(5%, 20 candidates) by frozen model score
```

All Route C ranking comparisons use:

```text
same structures
same model scores
same threshold rule
same matched denominator
only the DFT label source changes
```

## Route C Reopen Criterion

Route C can reopen the NMI discordance line only if all conditions hold:

```text
n_common >= 200
binary exact-stability discordance >= 0.40
alternative-frontier stable-F1 ranking flip exists
all primary Route C models score the same denominator
```

The ranking flip criterion is unchanged:

```text
top model changes OR at least one adjacent ordering flips
AND absolute stable-F1 delta >= 0.05 for an affected pair
```

## Route C Close Criterion

If Route C reaches `n_common >= 200` and the alternative-frontier stable-F1
ranking does not flip, the NMI discordance line remains closed. The result may
be retained as a source-discordance diagnostic but not launched as a standalone
NMI claim.

If Route C cannot assemble at least three eligible primary models before
outcome inspection, it is reported as reduced-panel diagnostic only unless the
protocol is explicitly amended before any ranking outcomes are computed.

## Forbidden Moves

- Do not call Route C a Route B result.
- Do not add or remove models after seeing Route C ranking metrics.
- Do not use different denominators per model in the primary ranking endpoint.
- Do not use formula-only matches in the primary denominator.
- Do not claim ALIGNN-FF failed scientifically; only its scorer readiness
  failed in the current environment.
- Do not relax the stable-class F1 endpoint.
- Do not promote CHGNet/MACE-only results to full primary frontier-panel
  evidence.
