# Submission-Ready Discordance Diagnostics

This milestone adds the requested denominator audit and robustness diagnostics
without changing the core claim boundary.

## Added Artifacts

- denominator construction audit for the MP-vs-Alex exact-match set;
- representativeness source data for cell size, elements, crystal system and
  e_above_hull distributions;
- formal WBM-vs-Alex case-analysis definition;
- uncertainty-threshold sweep for near-hull flags;
- uncertainty-filtered benchmark metrics and model-rank stability;
- selection-fraction discordance curves with bootstrap and random-ranking nulls;
- logistic/permutation diagnostics for model-rank amplification;
- MP-vs-Alex scatter source data and top discordant cases;
- third-source coverage closeout.

## Claim Boundary

The durable finding remains modest and scoped: MP-vs-Alex discordance is about
10.8% on the strict denominator, is concentrated near the hull, and is not
robustly amplified by the tested ML model high-score regions. OQMD/JARVIS do
not currently provide a completed third-source measurement.
