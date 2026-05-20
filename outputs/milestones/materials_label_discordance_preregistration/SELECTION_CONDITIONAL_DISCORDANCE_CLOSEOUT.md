# Selection-Conditional Discordance Diagnostic

## Question

Does MP-vs-alex label discordance concentrate in the candidates that ML models
rank as most stable?

## Input

```text
denominator: Route B MP-vs-alex strict-structure matches
n_common: 287
models: ALIGNN-FF | CHGNet | MACE-MP
score direction: lower score = more stable
```

## Gate

The NMI launch gate for this refined hypothesis requires at least two models to
show:

```text
top-decile discordance >= 0.30
enrichment over full-denominator baseline >= 2.0
permutation p <= 0.10
```

## Result

```text
launch_gate: NO_GO
models_passing: 
```

This result is a diagnostic of the refined selection-conditional hypothesis. It
does not alter the Route B full-snapshot no-go result unless the gate passes.
