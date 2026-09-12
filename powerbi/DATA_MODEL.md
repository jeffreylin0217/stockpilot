# StockPilot Power BI data model

**Current artifact status:** reporting CSVs, a model specification, DAX definitions and build instructions exist. No PBIX/PBIT or screenshots are present. This document specifies the model the report can use; it does not claim an implemented Power BI semantic model.

## Model choice
Use `daily_sales` as the primary historical fact. Its grain is **one date × store_nbr × family**. Create three small lookups inside Power BI: `DimStore`, `DimFamily`, `DimDate`. Connect the first two to both the historical fact and the separate `reorder_risk` snapshot. Only the historical fact gets a date relationship.

All other imported CSVs are deliberately disconnected reference/reporting tables. They are useful for full-run checks, not substitutes for filter-responsive demand measures. Do not join facts to facts, append totals to daily records, or use summary totals as dimension attributes. This follows Microsoft's [star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) and [relationship guidance](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand).

## Every export: grain, role and columns
Exact table names are the filenames without `.csv`. Column names below were inspected in regenerated sample exports.

| File / table | Grain | Role and relationship behavior |
|---|---|---|
| `daily_sales.csv` | date × store_nbr × family | Main fact; all three lookups filter it |
| `weekly_sales.csv` | Monday-start week × store_nbr × family | Disconnected aggregate reference; use daily fact plus DimDate[Week Start] for interactive weekly charts |
| `family_performance.csv` | family, full run | Disconnected totals for reconciliation; not an interactive dimension |
| `store_performance.csv` | store_nbr, full run | Disconnected totals for reconciliation; not an interactive dimension |
| `promotion_impact.csv` | family, full run | Disconnected descriptive promotion summary; dynamic analysis uses measures on daily_sales |
| `demand_volatility.csv` | family, full run | Disconnected daily aggregate variability across all observed stores/dates |
| `reorder_risk.csv` | store_nbr × family, latest as-of snapshot | Planning fact; store/family lookups filter it, historical dates do not |
| `recommendations.csv` | one qualifying suggestion, full run | Disconnected text report; `scope` is display text, not a dependable relationship key |
| `overview_kpis.csv` | one named metric, full run | Disconnected validation/reference table; do not sum different metric values |
| `quality_summary.csv` | one metadata key, full run | Disconnected source/assumptions table; `value` is mixed text/JSON, not a numeric fact |

### Column contract and Power Query types

- **daily_sales:** `date` Date; `store_nbr`, `weekday_number` Whole number; `family`, `day_type` Text; `sales`, `onpromotion` Decimal number; `promoted` True/False (nullable). Promotion count is stored numerically; unknown stays null.
- **weekly_sales:** `week` Date; `store_nbr`, `observed_days` Whole number; `family` Text; `sales` Decimal number.
- **family_performance:** `family` Text; `total_sales` Decimal number; `observed_days` Whole number.
- **store_performance:** `store_nbr`, `observed_days` Whole number; `total_sales`, `average_daily_sales` Decimal number.
- **promotion_impact:** `family` Text; `promoted_rows`, `nonpromoted_rows` Whole number; `promoted_average`, `nonpromoted_average`, `lift_pct` Decimal number, allowing null. `lift_pct` is already multiplied by 100: 31.24 means 31.24%, not 3,124%.
- **demand_volatility:** `family` Text; `daily_mean`, `daily_std`, `coefficient_of_variation` Decimal number, allowing null where undefined. The last is a ratio, not percent change.
- **reorder_risk:** `store_nbr`, `observed_days` Whole number; `family`, `forecast_quality`, `inventory_source`, `risk` Text; `last_observed_date`, `forecast_date` Date; `recent_average`, `demand_std`, `coverage`, `expected_lead_time_demand`, `safety_stock`, `reorder_point`, `target_stock_level`, `inventory_on_hand`, `days_of_supply`, `reorder_quantity` Decimal number. Retain nulls for insufficient history/undefined ratios. Coverage 1.0 means 100% of the recent calendar window is observed.
- **recommendations:** `scope`, `evidence`, `recommendation` Text. This export may legitimately be empty for another source.
- **overview_kpis:** `metric` Text, `value` Decimal number. Current metric keys: `Total demand volume`, `Product families`, `Stores`, `Reorder now series`.
- **quality_summary:** `check`, `value` Text. Current keys: `source`, `data_label`, `rows`, `kpis`, `planning`, `warnings`, `as_of`. Nested objects are JSON strings; retain them as readable text unless you intentionally expand them in Power Query.

Use Date, not a datetime hierarchy, for date keys. Use decimal rather than currency formatting for demand. Do not convert missing numbers to zero. Set identifiers and snapshot-detail numbers to **Don't summarize** when used as table fields.

## Lookup construction
1. In Power Query, right-click `daily_sales` → **Reference**. Rename to `DimStore`; keep only `store_nbr`; remove duplicates. Check for non-null unique keys.
2. Reference `daily_sales` again as `DimFamily`; keep only `family`; remove duplicates. These are category names, not item identifiers. There is no city/state export to add automatically.
3. Create `DimDate` using the exact calculated-table and calculated-column definitions in [REPORT_BUILD_GUIDE.md](REPORT_BUILD_GUIDE.md). It covers complete calendar years and has one row per day. Mark it as a date table using `DimDate[Date]`.

No combined store-family string key or bridge is necessary: independent store and family filters intersect in each fact. Avoid using `reorder_risk` as a dimension for historical sales.

## Exactly five active relationships

| One side (unique key) | Many side | Cardinality | Cross-filter direction |
|---|---|---|---|
| DimStore[store_nbr] | daily_sales[store_nbr] | One-to-many (1:*) | Single, lookup → fact |
| DimFamily[family] | daily_sales[family] | One-to-many (1:*) | Single, lookup → fact |
| DimDate[Date] | daily_sales[date] | One-to-many (1:*) | Single, lookup → fact |
| DimStore[store_nbr] | reorder_risk[store_nbr] | One-to-many (1:*) | Single, lookup → snapshot |
| DimFamily[family] | reorder_risk[family] | One-to-many (1:*) | Single, lookup → snapshot |

Remove any automatically detected extra relationships. No bidirectional or many-to-many relationships are required. Hide fact-side store/family keys in the field list after table layouts are built if that helps prevent accidental fact-field slicers. Use dimension fields in slicers and cross-fact axes.

## Filter contracts that make the report truthful
- **Pages 1–4:** use DimDate, DimStore, DimFamily. Calculate historical cards/charts from daily_sales so they respond together. Observed Days counts fact dates, not all calendar dates; an unobserved day is unknown, not zero.
- **Page 5:** use DimStore, DimFamily and reorder_risk[risk]/[inventory_source]. No date slicer, including hidden synchronized slicers. Display Snapshot As Of and Planning Assumptions. A date filter does not rerun Python, recalculate lead-time assumptions or recreate inventory.
- **Page 6:** recommendations is full-run text without structured store/family/date keys. Only a searchable recommendations[scope] slicer is supported. Never parse its sentences to manufacture joins. For structured filtered review use the planning table on page 5.
- **Page 7 and reference visuals:** disconnected tables show the entire last run. Label them “Full pipeline run — not affected by historical slicers.” Date/store/family slicers do not filter them. Do not imply otherwise through visual placement.

Precomputed family-level standard deviations cannot simply be summed to produce total demand variability. Their mean is only an equal-weight description of those family statistics. Store/family summaries are not automatically filterable by date. Promotion lift should be recomputed from daily rows for selections; never average exported percentages to obtain a combined lift.

## Refresh and limitations
Run the sample pipeline, then the export script, then Refresh in Desktop. All files are overwritten with the latest run. They contain no multi-run snapshot history. Old exported files are not proof that a new pipeline run succeeded. If interrupted, rerun both commands fully before refreshing. CSV typing and the five relationships must be checked after a schema change.

The delivered Python tests check exported keys, numeric fields and reconciliation. They do not validate DAX compilation, relationship settings, visuals, interaction behavior or refresh in Desktop. Those require the manual acceptance checks in the build guide.
