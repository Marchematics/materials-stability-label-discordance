# Full MP-Alex Denominator Run

This milestone processes all Alexandria v20 rows with MP identifiers. It is separate from the frozen 287-row Route-B diagnostic and does not overwrite those artifacts.

The public-safe artifact set commits the strict-match CSV and summary tables. The full MP structure JSONL cache is retained locally for resumability and is excluded from git because it is a large raw API cache, not a paper-facing table.

|   alex_mp_identifier_rows |   mp_records_successfully_queried |   reduced_formula_matches |   strict_structure_matches |   mp_alex_labels_available |   discordant_n |   discordance_rate | claim_scope                          |
|--------------------------:|----------------------------------:|--------------------------:|---------------------------:|---------------------------:|---------------:|-------------------:|:-------------------------------------|
|                     43984 |                             43169 |                     43169 |                      43139 |                      43139 |           5060 |           0.117295 | full_43984_MP_identifier_denominator |
