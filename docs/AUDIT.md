# Verification audit

Verified locally on 2026-09-11 after adding the sample business review and reproducible analytical preview.

## Executed checks

- `python -m stockpilot.pipeline --source sample`: succeeded.
- `python scripts/export_powerbi.py`: succeeded.
- `pytest -q`: **34 passed in 0.54s**.
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
- Planning classifications: 3 Reorder now, 3 Monitor, 3 Healthy, 3 Overstock risk; 0 Insufficient history

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

## Implementation scope

The core pipeline, SQL models and exporter implementation were preserved. The analytical presentation layer adds business questions, a sample findings brief, a Python-generated chart and its optional plotting dependency. The existing Power BI model, DAX and export tests remain unchanged.

## Analytical preview checks

- `python scripts/build_sample_brief.py`: succeeded against the sample in temporary storage.
- All four statements in `sql/business_questions.sql` executed successfully against the generated DuckDB database: 3, 12, 4 and 9 rows respectively.
- Preview risk counts reconcile to all 12 planning rows; unknown risk labels fail generation rather than silently dropping rows.
- The trend uses 17 complete weeks; the final one-day week is excluded.
- The PNG was visually inspected for labels, clipping and agreement with the source results. It is a Python chart, not a Power BI screenshot.
- The findings report reproduces store 3's 39.2% demand share, Household CV 0.320 and family promotion comparisons directly from pipeline outputs.

## What this audit does not establish

No PBIX/PBIT or report screenshots were created. Power BI Desktop has not executed the DAX, relationships or visuals. A completed report requires building it using `powerbi/REPORT_BUILD_GUIDE.md`, performing the reconciliation and filter checks, and saving a verified `powerbi/StockPilot.pbix`.

The full Kaggle public dataset has not been validated here.

Forecast accuracy has not been measured on a chronological holdout.

No actual stockout reduction, business adoption, causal promotion effect, revenue impact or stakeholder outcome is claimed.
