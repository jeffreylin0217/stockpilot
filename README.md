# StockPilot — Retail Demand & Inventory Analytics

StockPilot is a **Python/SQL + Power BI retail demand and inventory analytics project** for an analyst/Industrial Engineering portfolio. It analyzes store and product-family demand, promotion associations, variability and explainable replenishment scenarios.

**Current data:** 1,440 synthetic daily observations, 3 stores, 4 product families, 120 days. **Current reporting deliverables:** ten CSV exports, a Power BI data model specification, commented DAX and a seven-page build guide. **There is no PBIX/PBIT in this repository yet.** The business-facing Power BI report will be built manually afterward.

```text
Synthetic / compatible public demand source
→ Python validation and loading
→ DuckDB SQL Bronze / Silver / Gold analytics
→ Python forecasting and replenishment calculations
→ Power BI reporting exports
→ Power BI business-intelligence report (manual build pending)
```

An analyst can use the planned report to compare demand patterns and prioritize inventory review. Sales is demand volume, not revenue; the demo inventory is simulated. No actual stockout reduction, forecast-accuracy improvement, stakeholder adoption or company results are claimed.

## Quick start
Use Python 3.10 or later. Run these commands from this project directory. The editable installation makes `stockpilot` importable without setting PYTHONPATH.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m stockpilot.pipeline --source sample
python scripts/export_powerbi.py
pytest -q
```

On Windows activate with `.venv\Scripts\activate`. The repository is intended for an editable installation so the Python package and SQL files remain available from the project root.

```bash
# Auto-select raw/train.csv when present; otherwise sample/train.csv
python -m stockpilot.pipeline
# Explicit source; invalid real data fails instead of silently becoming demo data
python -m stockpilot.pipeline --source raw
# Compare explainable assumptions by rebuilding the snapshot
python -m stockpilot.pipeline --source sample --window 14 --lead-time 7 --review-days 7 --z-score 1.65
# Recreate the same demo observations
python scripts/generate_sample.py
```

The pipeline replaces its own generated schemas and exports on each successful run. Close any external DuckDB connection before rebuilding if DuckDB reports a file lock. Required-data validation happens before database writes; SQL writes use a transaction. Export files are written after commit, so rerun if interrupted while exporting.

## Dataset options
The included data has 1,440 synthetic daily observations across 3 stores, 4 categories and 120 days. Its patterns were deliberately generated for demonstration. Source and inventory provenance appear in the quality report and can be surfaced in the Power BI reporting layer. It is not a substitute for validation on public retail data.

To use real data, visit the official [Kaggle Store Sales — Time Series Forecasting data page](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data), sign in and accept the applicable dataset/competition terms. Download and extract `train.csv` into `data/raw/`. Optionally include `stores.csv`, `transactions.csv`, `oil.csv` and `holidays_events.csv` in that same directory. No credentials or paid API are required by the code. `test.csv` has no observed target sales and is deliberately not ingested as history; competition submissions are outside this project's scope.

Required train columns: `date` (YYYY-MM-DD), `store_nbr` (positive integer), `family` (nonblank category), `sales` (finite nonnegative volume). Optional `onpromotion` is a nonnegative count; any positive value marks a promotion-associated row. Grain is exactly one date/store/family. Extra columns are preserved in Bronze/Silver, but not necessarily used in Gold. Invalid required data raises an actionable error. Invalid optional files are skipped with warnings; absent optional files are safe.

An optional `inventory.csv` may contain `date,store_nbr,family,inventory_on_hand` in the same source directory. Stock must be nonnegative, use demand-compatible units, and be unique at that grain. Only an exact snapshot matching the latest sales date is used; unmatched series receive an explicitly labeled simulated scenario. The code cannot independently verify a supplied stock file. Store, holiday, oil and transaction data are retained in Bronze/Silver for future analysis, not multiplied into sales through potentially unsafe joins.

## Metrics and assumptions
- Sales is demand volume, not dollars. Aggregation across mixed category units is only a rough volume indicator.
- Average daily sales = total volume / observed distinct dates, not average transaction size or average row.
- Weekly totals start Monday; boundary weeks may be partial.
- Promotion lift = 100 × (mean promoted-row sales / mean nonpromoted-row sales − 1). Missing groups or a zero denominator produce undefined lift. This is descriptive association, not causal impact.
- Forecast = trailing 28-calendar-day average per store/family by default. Next-day expected demand equals `recent_average`; next lead-time demand equals mean × lead time.
- Daily variability uses sample standard deviation (ddof=1). Missing dates are unknown, not zero-filled. Incomplete series receive `Insufficient history` and no actionable reorder quantity. Full coverage is not forecast accuracy or statistical confidence.
- The forecast window must be at least 2 days. Lead time defaults to 7 days; review period defaults to 7; z defaults to 1.65. These are visible assumptions, not empirically estimated parameters.
- Safety stock = z × daily standard deviation × √lead time. Reorder point = mean × lead time + safety stock.
- Target stock = mean × (lead + review days) + z × daily standard deviation × √(lead + review days). Quantity = max(0, target − on-hand).
- Monitor means stock from reorder point through 110% of that point. Reorder now means below it. Above 150% of target is Overstock risk; otherwise Healthy. These thresholds are planning heuristics. Zero demand gives undefined days of supply; positive stock with zero target is overstock.
- Synthetic inventory cycles through 0.5, 1.05, 1.4 and 4.0 times the reorder point in sorted store/family order. These scenarios are deliberately constructed, not estimates of actual on-hand.
- Power BI filters can support report-layer exploration, while persisted planning outputs represent the latest full-dataset pipeline snapshot.

## Folder structure

    stockpilot/
    ├── README.md
    ├── FILES.md
    ├── requirements.txt
    ├── pyproject.toml
    ├── data/
    │   ├── sample/
    │   ├── raw/
    │   └── processed/              # generated, ignored
    ├── powerbi/
    │   ├── README.md
    │   ├── DATA_MODEL.md
    │   ├── REPORT_BUILD_GUIDE.md
    │   ├── measures.dax
    │   ├── screenshots/.gitkeep    # real screenshots only, trackable
    │   └── exports/                # generated, ignored
    ├── scripts/
    │   ├── generate_sample.py
    │   └── export_powerbi.py
    ├── sql/
    │   ├── bronze.sql
    │   ├── silver.sql
    │   └── gold.sql
    ├── src/stockpilot/
    │   ├── config.py
    │   ├── data_loader.py
    │   ├── validation.py
    │   ├── metrics.py
    │   ├── forecasting.py
    │   ├── inventory.py
    │   ├── recommendations.py
    │   └── pipeline.py
    ├── tests/
    │   ├── test_validation.py
    │   ├── test_metrics.py
    │   ├── test_inventory.py
    │   ├── test_pipeline.py
    │   └── test_powerbi_exports.py
    └── docs/
        ├── ARCHITECTURE.md
        └── AUDIT.md

## Limitations and next steps
No measured forecast accuracy or business outcome is claimed. The baseline ignores trend, seasonality, promotion changes and stockout-censored demand. Safety stock assumes independent daily demand, fixed lead time and an approximate normal model; z=1.65 does not demonstrate 95% achieved service. Category-level volumes and inventory do not represent individual substitutable SKUs. Inventory position omits inbound orders, reservations, backorders, order packs, shelf life and costs.

After adding Kaggle data: run `--source raw`, review the quality report and coverage, inspect date/grain/unit assumptions, and revisit recommendations. The Python pipeline loads source data into pandas before producing analytical outputs, so memory may be significant; full Kaggle-scale performance has not been measured. Before claiming forecast quality, add rolling-origin holdouts comparing 7/14/28-day and same-weekday baselines using MAE/WAPE (handle zero demand). Before claiming simulated stockout reduction, build a documented inventory simulation with a fixed policy comparator. Before business use, obtain SKU-level stock and lead times and validate with an authorized stakeholder.

## Resume honesty
For the included version say **synthetic retail data**. Only say **public retail data** after running and reviewing a public dataset. Do not claim real business impact, adoption, dollars saved, improved forecast accuracy, stockout reductions or stakeholder work without evidence.

## Power BI Reporting

Power BI is the intended presentation and decision-support layer. The repository currently contains reporting datasets and specifications, **not an existing Power BI report**.

Regenerate every reporting file from the project root:

```bash
python -m stockpilot.pipeline --source sample
python scripts/export_powerbi.py
pytest -q
```

The ten generated CSVs in `powerbi/exports/` are `daily_sales`, `weekly_sales`, `family_performance`, `store_performance`, `promotion_impact`, `demand_volatility`, `reorder_risk`, `recommendations`, `overview_kpis` and `quality_summary`. They remain ignored because they are reproducible.

The planned pages are Executive Overview, Demand Trends, Store & Product-Family Performance, Promotion Analysis, Inventory Planning, Recommendations, and Data Quality & Assumptions. Use the [manual report build guide](powerbi/REPORT_BUILD_GUIDE.md), [data model](powerbi/DATA_MODEL.md) and [DAX measures](powerbi/measures.dax). The [Power BI README](powerbi/README.md) gives the build order.

In Desktop, create store/family/date lookups for the daily fact, with store/family relationships also filtering the separate planning snapshot. Keep full-run summaries and recommendation text disconnected. Historical filters must not imply recalculated inventory. The build guide explains these boundaries and provides sample acceptance values.

Save a future real file at `powerbi/StockPilot.pbix` and actual screenshots under `powerbi/screenshots/`; neither is ignored. After personally building, reopening and verifying the report, replace the “no PBIX yet” wording here with a link to the real file and record the manual checks in [docs/AUDIT.md](docs/AUDIT.md). Until then, use only the pre-PBIX resume wording.

## Verification

The current sample pipeline and all ten reporting exports were regenerated successfully. **34 pytest tests passed**; compile and whitespace checks also passed. Export tests validate actual columns, key uniqueness, numeric values, reconciliation and preservation of undefined metrics. DAX definitions and the model are documented but have **not been executed in Power BI Desktop**. See [the audit](docs/AUDIT.md) for results and manual validation still required.
