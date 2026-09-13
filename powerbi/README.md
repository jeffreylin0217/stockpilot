# Power BI reporting layer

**Delivered:** ten CSV reporting datasets, a documented model, commented DAX measures, and a seven-page manual report specification. **Not delivered:** a PBIX/PBIT, an executed Desktop semantic model, or screenshots. Power BI is the intended business-facing reporting layer; The report can be built and verified the actual report in Desktop.

## Build in this order
1. Regenerate the exports from the project root:
   ```bash
   python -m stockpilot.pipeline --source sample
   python scripts/export_powerbi.py
   pytest -q
   ```
2. Read [DATA_MODEL.md](DATA_MODEL.md) for every export's grain, column types and the five relationships.
3. Follow [REPORT_BUILD_GUIDE.md](REPORT_BUILD_GUIDE.md) to import CSVs, create lookups and build the pages.
4. Add the definitions in [measures.dax](measures.dax), one measure at a time. They require manual compilation and validation in Desktop.
5. Save the actual report as `powerbi/StockPilot.pbix`. Add only your own real captures to `powerbi/screenshots/`. Both are trackable; generated `exports/` files stay ignored.

## Reporting datasets
| Dataset | Intended role |
|---|---|
| daily_sales.csv | Primary historical fact, date/store/family |
| reorder_risk.csv | Latest store/family planning snapshot |
| weekly_sales.csv | Full-run weekly reconciliation |
| family_performance.csv, store_performance.csv | Full-run performance reconciliation |
| promotion_impact.csv, demand_volatility.csv | Full-run descriptive summaries |
| recommendations.csv | Standalone recommendation text |
| overview_kpis.csv | Standalone mixed-unit KPI reference |
| quality_summary.csv | Standalone source and assumptions metadata |

Do not join every CSV just because the columns have similar names. The daily fact supplies interactive demand measures. The planning fact responds to store/family selections but not historical dates. Recommendation text and stored summaries remain full-run references.

## Seven intended pages
Executive Overview; Demand Trends; Store & Product-Family Performance; Promotion Analysis; Inventory Planning; Recommendations; Data Quality & Assumptions. The build guide specifies fields, measures, slicers, chart types, limitations and manual acceptance values for each.

## What the current data supports
The included demo contains 1,440 synthetic daily observations across 3 stores and 4 product families over 120 days. `sales` means demand volume, not revenue. Inventory is simulated in the demo; the optional exact-date supplied-inventory pathway retains its provenance label. Lead time, review period and safety-stock parameters are assumptions. Promotions are descriptive associations. Forecast accuracy has not been evaluated against a chronological holdout. Store Sales/Favorita-compatible input remains the intended public-data path and has not been verified at full scale in this audit.

## Current verification boundary
34 pytest tests pass, including real sample pipeline/export integration. Python verifies CSV contents and arithmetic, not Power BI visuals, DAX execution, filter interactions or Desktop refresh. No completed Power BI report or company result is claimed. After the manual build, update the status in this file, the root README and docs/AUDIT.md to reflect the actual saved artifact and checks.
