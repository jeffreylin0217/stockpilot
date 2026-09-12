# Architecture

The flow is CSV files → Python validation → DuckDB Bronze/Silver → SQL Gold marts → Python forecast/planning → CSV reporting exports → manually built Power BI report (pending). The analytical pipeline remains local and does not require service infrastructure.

## Responsibilities
`config.py` defines the project root and validates planning parameters. `data_loader.py` selects one source directory and loads CSVs. Required sales failures stop the run; missing or invalid optional context produces warnings. The program never combines synthetic and real sales. `validation.py` validates dates, finite/nonnegative quantities, keys and uniqueness before modeling. Whitespace is trimmed from family names before checking duplicates.

Bronze tables preserve loaded values (pandas still infers CSV types; these are not byte-for-byte archives). Original CSVs remain the authoritative raw input. Silver tables contain validated pandas types. Python creates the dynamic optional tables; `bronze.sql` and `silver.sql` own schema creation. `gold.sql` uses GROUP BY, conditional aggregates, date_trunc, isodow and nullif to build daily, weekly, store, family, promotion and volatility tables. Optional context is stored separately to prevent holiday or transaction joins from duplicating category sales.

`forecasting.py` computes trailing-calendar-window statistics per store/category. `inventory.py` computes reorder scenarios, checks exact-date stock snapshots and labels sources. `recommendations.py` turns measurable conditions into conservative review suggestions. `pipeline.py` orchestrates these steps, saves `gold.reorder_risk`, `gold.recommendations` and `gold.run_metadata`, and exports CSVs and JSON. The database update is transactional; file exports follow the commit.

The pipeline exports daily, weekly, performance, promotion, volatility and inventory-planning datasets for the Power BI reporting layer. SQL marts remain available for reproducible queries and exports. Tests verify numerical logic, pipeline behavior and compatibility between the analytical outputs and Power BI export layer.

## Gold table grain
| Table | Grain / purpose |
|---|---|
| daily_sales | date × store × family, typed demand and calendar features |
| weekly_sales | Monday-start week × store × family, totals and observed days |
| store_performance | store, total volume and observed-day average |
| family_performance | family, total volume and observed days |
| promotion_impact | family, conditional averages, group sizes and lift |
| demand_volatility | family, mean/std/CV of daily aggregate volume |
| reorder_risk | store × family, latest forecast and planning scenario |
| recommendations | qualifying review suggestion with evidence |
| run_metadata | one JSON report containing source, as-of date and parameters |

## Why these technologies
Python orchestrates files and business formulas; pandas handles small readable transformations. SQL makes grouping and conditional aggregation inspectable. DuckDB runs analytical SQL in a single local file without managing a server. Power BI is the intended business-facing reporting and visualization layer. pytest checks known numerical answers, pipeline behavior and reporting-export compatibility. There is no ML dependency because the moving average is the model.

## Failure handling and scale
Required data errors stop before replacing the last valid database. Optional errors are visible in metadata. SQL errors roll back when the connection closes. An interrupted CSV export can leave mixed export versions; rerun the pipeline. Close external DuckDB connections before batch updates to avoid process locks. The current implementation favors explainability over streaming ingestion; memory and runtime on the full public dataset remain to be measured.

## Reporting model and calculation ownership
The reporting layer now includes `powerbi/DATA_MODEL.md`, `powerbi/measures.dax` and `powerbi/REPORT_BUILD_GUIDE.md`. No PBIX exists. These specify a small model with daily_sales as the main historical fact, a distinct planning snapshot and three manually created lookups. There are five single-direction relationships. Full-run summaries and recommendation text stay disconnected to prevent misleading filter behavior.

Python and SQL own validation, aggregation, variability, forecast and inventory formulas. DAX owns context-sensitive display totals, ratios and counts. Dynamic promotion comparisons reproduce the SQL definition for selected data. DAX does not execute Python, retune a forecast or reconstruct historical inventory. The report will refresh the exported snapshot only after the pipeline and export script run successfully.

The Power BI export tests verify real pipeline tables and reconcile their totals, including optional-data blank behavior. Desktop model/DAX/visual tests remain manual. The source and instructions are version controlled; generated data is ignored, while a future real PBIX and authentic screenshots are trackable.

## GitHub analytical preview

`scripts/build_sample_brief.py` runs the existing sample pipeline in a temporary directory, then uses pandas and optional Matplotlib to produce `docs/SAMPLE_FINDINGS.md` and `docs/images/sample-analysis.png`. It does not change the current processed database or Power BI exports. This deliberately small presentation layer exposes the analysis on GitHub before a real Power BI report is built. `sql/business_questions.sql` contains standalone, read-only queries for investigating the same business questions.
