# Audit Change Log — 2026-10-30

## Research-result and audit corrections

1. Reconciled the AtCoder descriptive table with the supplied fixed-cohort audit output using query-weighted means across reference-selection seeds 0–4.
2. Corrected the manuscript's headline AtCoder Success@1 values: Mean is 0.2046 at k=1, 0.3954 at k=5, 0.4572 at k=10, and 0.5070 with all references. Max is 0.2046, 0.3417, 0.3932, and 0.4527.
3. Kept AtCoder task-level bootstrap comparisons identified as task-weighted, rather than mixing them with the query-weighted descriptive table.
4. Added reference-seed variability of AtCoder Success@1 to the Table 2 note.
5. Saved the supplied AtCoder fixed-cohort audit report as valid JSON for machine-readable inspection.

## Scope of verification

The reported result corrections are based on the supplied Colab audit output. They are not an independent third-party replication. CoREB and filtering claims remain as reported in the manuscript and supplied audit artifacts.

## Packaging changes

This release uses a flat repository layout: every project file is stored in the root directory. This avoids folder-upload path mismatches and eliminates relative Markdown hyperlinks from the README and run guide. The standalone AtCoder script and AtCoder audit notebook both save their report in the repository root by default. The archive path recorded in the saved JSON has been reduced to the dataset filename rather than a machine-specific Colab path. The CoREB loaders use the same immutable dataset revision.

Packaging validation checks file presence, Notebook JSON validity, Python syntax, internal Markdown-link absence, checksum consistency, and ZIP integrity. **No raw-data rerun or independent replication was performed during this packaging update.**
