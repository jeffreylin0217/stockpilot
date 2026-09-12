# Synthetic demo data
These are deterministic, generated observations, NOT Kaggle or Corporación Favorita records.
3 stores × 4 families × 120 days (2024-01-01 through 2024-04-29) = 1,440 rows.
Sales encode weekly patterns, promotion associations and varying category noise solely to exercise the pipeline and reporting specifications.
Regenerate identically with `python scripts/generate_sample.py`. All simulated inventory is created by the pipeline and labeled in every output row.
