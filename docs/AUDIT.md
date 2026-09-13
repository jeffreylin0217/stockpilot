# Verification audit

Verified locally on 2026-09-13 after adding the StockPilot Power BI reporting specification.

## Executed checks

- `python -m stockpilot.pipeline --source sample`: succeeded.
- `python scripts/export_powerbi.py`: succeeded.
- `pytest -q`: **34 passed in 0.34s** (31 retained tests and 3 new export tests).
- Python compilation checks for `src`, `scripts`, and `tests`: succeeded.
- `git diff --check`: succeeded.
- Export tests check actual pipeline schemas, keys, numeric values, reconciled totals and promotion groups, and preservation of missing promotion and planning values.
- All 14 distinct qualified table/column references in `powerbi/measures.dax` match generated CSV headers. This is a static schema check, not DAX execution.
- Future real PBIX/PBIT files and screenshots are not ignored; generated exports remain ignored.

## Reproducible demo scope

- 1,440 synthetic daily observations
- 3 stores
- 4 product families
- 120 dates
- Total synthetic demand volume: 176,589.03
- 12 inventory-planning series
- Simulated inventory when verified inventory-on-hand is unavailable
- Dates: 2024-01-01 through 2024-04-29
- Average daily network demand: 1,471.57525
- Promoted demand: 44,173.11 (25.0146% of total demand)
- Planning classifications: 3 Reorder now, 3 Monitor, 3 Healthy, 3 Overstock; 0 Insufficient history

## Generated export results

All ten exports were generated successfully:

| Export | Rows |
|---|---:|
| daily_sales.csv | 1,440 |
| weekly_sales.csv | 216 |
| family_performance.csv | 4 |
| store_performance.csv | 3 |
| promotion_impact.csv | 4 |
| demand_volatility.csv | 4 |
| reorder_risk.csv | 12 |
| recommendations.csv | 7 |
| overview_kpis.csv | 4 |
| quality_summary.csv | 7 |

Optional transactions, oil, holidays/events and inventory files were absent from the sample run, as reported by the pipeline. The run succeeded with those documented warnings.

## Git and implementation scope

Changes are local and uncommitted. No commit, push, history rewrite or GitHub settings change was performed. HEAD and the locally recorded origin/main remain at `6eb1963f2d5151718de74a8cd8c84ba5a29db637`. This does not assert a fresh network fetch of the remote.

The core pipeline, SQL models and exporter implementation were preserved. Changes cover reporting documentation, DAX specifications, ignore rules and export tests.

## What this audit does not establish

No PBIX/PBIT or report screenshots were created. Power BI Desktop has not executed the DAX, relationships or visuals. The user must build the report using `powerbi/REPORT_BUILD_GUIDE.md`, perform its reconciliation and filter checks, and save a real `powerbi/StockPilot.pbix` before claiming a completed report.

The full Kaggle public dataset has not been validated here.

Forecast accuracy has not been measured on a chronological holdout.

No actual stockout reduction, business adoption, causal promotion effect, revenue impact or stakeholder outcome is claimed.
