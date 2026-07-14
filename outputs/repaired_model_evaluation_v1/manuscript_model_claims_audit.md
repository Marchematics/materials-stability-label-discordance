# Repaired M1 model-claim audit

- **supported** — M1 fixed-support cohort contains 31,872 rows. (`all_view_common_support_exclusion_audit.csv`)
- **supported** — Consensus is a separate 24,614-row selection policy. (`evaluation_support_and_coverage.csv`)
- **supported** — Archived raw energy rankings have MP-native AUROC below 0.5 for all four primary models. (`score_construct_validity_audit.csv`)
- **supported** — Repaired predicted-hull rankings have MP-native AUROC above 0.5 for all four primary models. (`score_construct_validity_audit.csv`)
- **supported** — MACE-MP has the highest point-estimate M1 AUROC for every fixed-support label view. (`metrics_fixed_support.csv`)
- **supported** — MP-native minus audit stable yield at K=1000 is positive for all four models in every paired bootstrap replicate. (`paired_label_view_differences_cluster_bootstrap.csv`)
