# Route B: One-Shot MP-vs-Alex Full Snapshot Rescue Protocol

This is the only allowed rescue path for the materials-label discordance
paper route.

## Purpose

The existing WBM-vs-alex exact-structure probe shows high binary stability
discordance, but the preregistered frontier-model stable-F1 ranking endpoint
did not flip. Route B asks whether a stronger denominator, built directly from
Materials Project records and an independently downloaded Alexandria/alex-mp
snapshot, changes that conclusion.

## Non-Negotiable Rules

1. Run this rescue at most once.
2. Do not change the primary label definition.
3. Do not change the primary metric.
4. Do not add new models after seeing results.
5. Do not use formula-only matches in the primary denominator.
6. Do not promote the line if the primary ranking endpoint does not pass.

## Frozen Endpoint

```text
source A: Materials Project API-derived public records
source B: independently downloaded Alexandria / alex-mp snapshot
match rule: strict StructureMatcher high-confidence matches
primary denominator: exact/high-confidence structure matches only
minimum denominator: n_common >= 200
primary label: stable iff e_above_hull <= 0 eV/atom
primary model set: ALIGNN-FF / CHGNet / MACE-MP
primary ranking metric: stable-class F1
co-primary robustness metric: balanced accuracy
threshold: top max(5%, 20 candidates) by frozen model score
```

## Reopen Criterion

Reopen the NMI discordance line only if both conditions hold:

```text
binary exact-stability discordance >= 0.40
AND
frontier-model stable-F1 ranking flip exists
```

The ranking flip criterion is unchanged:

```text
top model changes OR at least one adjacent ordering flips
AND absolute stable-F1 delta >= 0.05 for an affected pair
```

## Permanent Close Criterion

If the MP-vs-Alex full snapshot rescue has `n_common >= 200` and still lacks
the frontier stable-F1 ranking flip, permanently close the NMI discordance
line. Keep the work as a source-discordance diagnostic, not a standalone NMI
paper.

If `n_common < 200`, the rescue is inconclusive for NMI launch and the line
also remains closed until a genuinely larger, legally frozen denominator is
available. Do not relax the denominator floor.

## Current Data Inputs

```text
Materials Project: API smoke passed; use MP_API_KEY from environment only.
Alexandria/alex-mp: local alex_mp_20.zip available.
Existing scores: ALIGNN-FF public WBM predictions; CHGNet/MACE generated on
the prior exact-match denominator. For Route B, scores must be regenerated or
frozen on the new MP-vs-Alex denominator before label-specific metrics.
```

## Secret Policy

Materials Project API keys are never committed. Route B artifacts may record
query success, package versions, source row counts, source hashes, material
ids, public labels, and structure hashes, but never credentials.
