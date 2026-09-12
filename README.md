# StockPilot — Retail Demand & Inventory Analytics

An explainable Industrial Engineering / Analytics portfolio project for Jeffrey Lin. StockPilot turns daily retail demand observations into SQL analytics, promotion comparisons and replenishment scenarios. The purpose is to practice translating data into operations decisions that Jeffrey can explain in an internship interview.

**Included version: synthetic demo data, not real company results.** No stakeholder, business adoption, actual stockout reduction or revenue impact is claimed.

## Business problem and outputs
An operations analyst needs to see which stores and categories drive volume, where demand varies, and which inventory assumptions imply replenishment attention. StockPilot provides DuckDB analytical tables, Power BI-ready reporting datasets, inventory-planning outputs, a quality report, practical tests and interview guides. Category-level planning is educational: it does not issue purchase orders.

## Quick start
Use Python 3.10 or later. Run these commands from this project directory. The editable installation makes `stockpilot` importable without setting PYTHONPATH.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m stockpilot.pipeline --source sample
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
        ├── INTERVIEW_GUIDE.md
        ├── RESUME_GUIDE.md
        ├── LEARNING_GUIDE.md
        └── AUDIT.md

## Limitations and next steps
No measured forecast accuracy or business outcome is claimed. The baseline ignores trend, seasonality, promotion changes and stockout-censored demand. Safety stock assumes independent daily demand, fixed lead time and an approximate normal model; z=1.65 does not demonstrate 95% achieved service. Category-level volumes and inventory do not represent individual substitutable SKUs. Inventory position omits inbound orders, reservations, backorders, order packs, shelf life and costs.

After adding Kaggle data: run `--source raw`, review the quality report and coverage, inspect date/grain/unit assumptions, and revisit recommendations. The Python pipeline loads source data into pandas before producing analytical outputs, so memory may be significant; full Kaggle-scale performance has not been measured. Before claiming forecast quality, add rolling-origin holdouts comparing 7/14/28-day and same-weekday baselines using MAE/WAPE (handle zero demand). Before claiming simulated stockout reduction, build a documented inventory simulation with a fixed policy comparator. Before business use, obtain SKU-level stock and lead times and validate with an authorized stakeholder.

## Resume honesty
For the included version say **synthetic retail data**. Only say **public retail data** after running and reviewing a public dataset. Do not claim real business impact, adoption, dollars saved, improved forecast accuracy, stockout reductions or stakeholder work without evidence. See `docs/RESUME_GUIDE.md`; learn and be able to modify the project before presenting it as your work.

## Power BI Reporting

StockPilot exports dashboard-ready CSV files for Power BI.

Generate the exports with:

```bash
python -m stockpilot.pipeline
python scripts/export_powerbi.py
```

The exported files are written to `powerbi/exports/`.

The inventory/reorder-risk section is simulated because the dataset does not include actual inventory-on-hand.
