# Build the StockPilot report in Power BI Desktop

**Status: manual build specification. No PBIX or PBIT has been created.** DAX and visual behavior must be checked in Desktop before claiming a completed report. This guide uses only exported columns inspected in the current sample run.

## 1. Prepare the files and Desktop

Power BI Desktop is a Windows application. On macOS, generate the CSVs here, then use a Windows computer or Windows environment with Desktop installed. Copy the project exports to that environment. No paid service publishing or scheduled refresh is required for this local report. See Microsoft's [Desktop installation requirements](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop).

From the StockPilot project root, with its Python environment active:

```bash
python -m stockpilot.pipeline --source sample
python scripts/export_powerbi.py
pytest -q
```

Confirm all ten CSVs exist in `powerbi/exports/`. Keep that directory in one stable location on Windows. The sample source should say `Synthetic demo data`; demand is volume, not money.

1. Open Desktop → **Blank report**.
2. **Home → Get data → Text/CSV** → select `daily_sales.csv` → **Transform Data**.
3. Rename the query `daily_sales` (no `.csv`). Confirm comma delimiter, UTF-8 text, and first-row column headers. If necessary use **Use First Row as Headers**.
4. In Power Query, **New Source → Text/CSV** for each of the other nine exports. Keep filenames without extensions as the query names. Do not use Combine Files: these files have different grains and schemas.
5. Apply the types in [DATA_MODEL.md](DATA_MODEL.md). Select date columns and use **Data type → Date**; use **Using Locale** if parsing reports errors. Sales metrics are Decimal number, not Currency; identifiers are Text/Whole number as specified. Convert `promoted` to True/False. Retain nulls instead of replacing them with zeros. Keep quality_summary[value] as Text even if automatic detection suggests a number.
6. Create `DimStore` and `DimFamily` by **Reference** to daily_sales, keep the single key, and **Remove Duplicates** as described in DATA_MODEL. Close & Apply.

## 2. Create the date lookup and relationships

In **Modeling → New table**, enter this definition (it is a calculated table, not a measure):

```dax
DimDate =
CALENDAR (
    DATE ( YEAR ( MIN ( daily_sales[date] ) ), 1, 1 ),
    DATE ( YEAR ( MAX ( daily_sales[date] ) ), 12, 31 )
)
```

Select DimDate and add each of these individually with **New column**:

```dax
Week Start = DimDate[Date] - WEEKDAY ( DimDate[Date], 2 ) + 1
```
```dax
Weekday Number = WEEKDAY ( DimDate[Date], 2 )
```
```dax
Weekday = FORMAT ( DimDate[Date], "dddd" )
```
```dax
Day Type = IF ( DimDate[Weekday Number] >= 6, "Weekend", "Weekday" )
```

Set Date and Week Start to Date type. Select Weekday → **Column tools → Sort by column → Weekday Number**. Mark DimDate as the date table with Date as its unique column. Complete-year coverage is intentional; averages still divide by observed fact dates. See Microsoft's [date-table guidance](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables).

In **Model view → Manage relationships**, create exactly the five active 1:* single-direction relationships listed in DATA_MODEL. Delete any auto-detected relationships to summary tables or between facts. Confirm arrows run from the lookup to the fact. No relationship uses forecast_date.

## 3. Add and format the measures

Open [measures.dax](measures.dax). Select daily_sales as the home table, then **Modeling → New measure** and paste **one measure definition at a time**, in file order. These are definitions, not a bulk DAX query; do not paste the entire file into DAX Query View. A measure can reference another table regardless of its home table.

- Demand, row averages, reorder points and quantities: decimal with 1–2 places and thousands separators; no currency symbol.
- Store/family/series/row counts: whole number.
- Promotion Share and Promotion Lift: Percentage, 1–2 decimals. These DAX ratios are fractions.
- Average Days of Supply: decimal, 1 place, days in the card title.
- Snapshot As Of: Date, `yyyy-MM-dd`.
- Average Demand Volatility (Full Run): decimal; title must include “full run”.

The exported `promotion_impact[lift_pct]` is already in percentage points. For an optional reference table use a decimal number with a `%` literal/custom format such as `0.00"%"`, or label it `Lift (%)`; do not apply the normal Percentage format. Do not average this column across families.

Core calculations remain in Python/SQL. The small dynamic promotion averages in DAX are necessary to support arbitrary date/store/family selections; they intentionally match the upstream comparison definition. See [CALCULATE](https://learn.microsoft.com/en-us/dax/calculate-function-dax) and [KEEPFILTERS](https://learn.microsoft.com/en-us/dax/keepfilters-function-dax) for how selections intersect.

## 4. Layout rules shared by all pages

Use a 16:9 canvas, a light background, dark readable text, and one blue accent for demand. Reserve red/amber for risk; pair color with text labels. Use page titles around 22–26 pt, labels around 11–12 pt, and 3–4 cards in a top row. Use two main charts below and a table only where it adds detail. Use standard visuals; no custom downloads or decorative scoring.

Add a small **Data Source Label** card and a text footer reading `Synthetic demo demand • Simulated inventory scenarios • Demonstration dataset` on every page for the sample build. Update the footer only after actually loading another source; keep the dynamic source card. Never title demand as revenue or use a pound/dollar symbol.

Use dimension fields for slicers. Sync DimDate, DimStore and DimFamily only across pages 1–4. Do not synchronize historical dates to page 5, including hidden slicers. Pages 6–7 use only their own standalone-table filters. Do not add report-level date/store/family filters that silently affect other pages. Set **Format → Edit interactions** so charts on pages 1–4 filter companion charts; inspect the resulting cards. Turn off interactions with any explicitly full-run reference visual if needed (the disconnected model already prevents fact filtering).

## Page 1 — Executive Overview

**Question:** How much demand is observed, over what period and assortment?

**Data:** daily_sales, DimDate, DimStore, DimFamily; quality_summary for the source label. Do not use overview_kpis[value] for responsive cards.

- **Cards:** Total Demand; Average Daily Demand; Store Count; Product Family Count.
- **Line chart:** X = DimDate[Date] (select the date field, not Date Hierarchy); Y = Total Demand; legend = none. Continuous X-axis; title `Daily demand volume`.
- **Clustered bar:** Y/category = DimFamily[family]; X/value = Total Demand; legend = none. Sort descending by Total Demand. If more than ten families, visual filter → family → Top N → Top 10 by Total Demand → Apply filter.
- **Slicers:** DimDate[Date] Between; DimStore[store_nbr] dropdown; DimFamily[family] dropdown.
- **Interpretation:** identifies scale, date coverage and the largest volume categories within the selection.
- **Caveat:** volume is not revenue or profit; average is per observed date across selected stores/families, not per transaction. Changing store coverage changes the total.

## Page 2 — Demand Trends

**Question:** How does demand vary by time and day of week?

**Data:** daily_sales and all three lookups. weekly_sales is a full-run reference only.

- **Cards:** Total Demand; Average Daily Demand; Observed Days.
- **Weekly line chart:** X = DimDate[Week Start]; Y = Total Demand; legend = DimFamily[family]. Limit the family selection to four or use a visual Top N filter of four by Total Demand for legibility. Title `Weekly demand — selected/top families`. Use the daily fact to honor exact date filters; do not add daily and weekly totals together.
- **Clustered column chart:** X = DimDate[Weekday]; Y = Average Daily Demand; legend = none. Monday–Sunday sorting uses Weekday Number.
- **Clustered bar chart:** Y/category = DimDate[Day Type]; X/value = Average Daily Demand; legend = none. Compare means rather than totals with unequal weekday/weekend counts.
- **Slicers:** date, store, family as on page 1.
- **Interpretation:** highlights timing and cadence that merit replenishment review.
- **Caveat:** first/last selected weeks can be partial. Missing source dates remain unknown. The complete calendar does not turn missing demand into zero. No seasonal forecast accuracy is claimed.

## Page 3 — Store & Product-Family Performance

**Question:** Which store/family combinations drive demand, and which full-run families vary most?

**Data:** daily_sales plus lookups for interactive performance; demand_volatility only for the explicitly separate snapshot panel.

- **Cards:** Total Demand; Store Count; Product Family Count.
- **Store bar:** Y/category = DimStore[store_nbr]; X/value = Total Demand; legend = none; descending sort.
- **Matrix:** rows = DimStore[store_nbr]; columns = DimFamily[family]; values = Total Demand, Average Daily Demand. Grand total average recalculates in total context; it is not the sum of row averages.
- **Small reference table below:** demand_volatility[family], [daily_mean], [daily_std], [coefficient_of_variation], each **Don't summarize**. Title `Family volatility — full pipeline run, all stores/dates`. Optional card Average Demand Volatility (Full Run) uses the same explicit label. Do not place this card among the dynamic historical KPIs.
- **Slicers:** date/store/family affect the bar/matrix/cards, not the full-run volatility reference. This exception must remain visible on the page.
- **Interpretation:** prioritize high-volume combinations; use the separate volatility table to investigate inconsistent demand.
- **Caveat:** rankings reflect assortment/coverage and volume, not productivity or profitability. The average of family standard deviations is not total-network volatility.

## Page 4 — Promotion Analysis

**Question:** How does observed demand differ between promotion-associated and nonpromoted rows?

**Data:** daily_sales with the three lookups. promotion_impact is an optional full-run validation table, not the basis of responsive visuals.

- **Cards:** Promoted Demand; Promotion Share; Known Promotion Rows.
- **Matrix/table:** rows = DimFamily[family]; values = Average Promoted Row Demand, Average Nonpromoted Row Demand, Promotion Lift, Promoted Row Count, Nonpromoted Row Count.
- **Clustered column chart:** X = DimFamily[family]; Y = Average Promoted Row Demand and Average Nonpromoted Row Demand; legend is the two measure names. Show a zero-based demand axis.
- **Slicers:** date/store/family. Do **not** add a promoted-only slicer: it would remove one comparison group. The strict `== FALSE()` DAX test intentionally excludes unknown promotion values.
- **Optional reference:** promotion_impact[family], [lift_pct], [promoted_rows], [nonpromoted_rows] as a separate table labeled full run, not affected by slicers.
- **Interpretation:** points to families worth further promotion review; always inspect the group counts.
- **Caveat:** onpromotion > 0 marks the whole row; family sales can include unpromoted products. Selection, timing and store mix confound lift. It is descriptive association, not incremental causal demand. Missing comparison groups and zero denominators yield blanks, not a measured 0% effect.

## Page 5 — Inventory Planning

**Question:** Which store/family scenarios merit replenishment review under the current assumptions?

**Data:** reorder_risk, DimStore and DimFamily. quality_summary supplies Planning Assumptions. These are latest-run planning outputs, not historical balances.

- **Cards:** Reorder Now Count; Monitor Count; Overstock Risk Count; Insufficient History Count. Add Snapshot As Of near the title and a readable Planning Assumptions card/text table below.
- **Clustered bar:** Y/category = reorder_risk[risk]; X/value = Planning Series Count; legend = none. This correctly intersects the selected risk with store/family filters.
- **Table:** reorder_risk[store_nbr], [family], [recent_average], [demand_std], [coverage], [forecast_quality], [inventory_source], [inventory_on_hand], [days_of_supply], [safety_stock], [reorder_point], [target_stock_level], [reorder_quantity], [risk], [forecast_date]. Use Don't summarize for numeric detail fields. Freeze narrow key columns where practical; allow horizontal scroll for detail.
- **Optional small summary cards:** Average Days of Supply, Average Reorder Point, Healthy Count, Series Requiring Attention. Show Total Recommended Reorder Quantity only in a single-family selection or label it `Mixed-family scenario quantity — not a purchase order`.
- **Slicers:** DimStore[store_nbr], DimFamily[family], reorder_risk[risk], reorder_risk[inventory_source]. **No historical date slicer.** Synchronize only store/family if desired; verify DimDate is not secretly synced.
- **Interpretation:** review the evidence for a scenario flag, then obtain actual inventory/lead-time information before an operational decision.
- **Caveat:** the sample's on-hand values are simulated; lead time/z/review days are assumed. Generic CSV mode may supply an exact-date stock snapshot, whose source remains visible but is not independently verified. DAX does not rerun forecasting when a slicer changes. Blank quantities under Insufficient history must not become zero. Attention count includes reorder, monitor and overstock; missing history is a separate QA count. Summed quantities include nonurgent rows below target stock.

## Page 6 — Recommendations

**Question:** What conservative review actions did the latest full pipeline run produce?

**Data:** recommendations and quality_summary only. No joins from scope text.

- **Cards:** Data Source Label. Use a quality_summary table filtered to check = `as_of` for the full-run timestamp; no numeric KPI is needed for this text report.
- **Primary visual:** table fields recommendations[scope], [evidence], [recommendation]. Turn on word wrap and make recommendation the widest column. Turn off totals. No chart is necessary.
- **Slicer:** recommendations[scope] dropdown with search enabled. Do not sync store/family/date slicers onto this page.
- **Interpretation:** provides a discussion agenda supported by persisted evidence.
- **Caveat:** title must read `Full-run recommendations`. These sentences do not recompute under exploration filters, and they are not purchase instructions. An empty recommendations file can legitimately mean no rule fired, rather than an import failure; distinguish using refresh/quality status.

## Page 7 — Data Quality & Assumptions

**Question:** What source and assumptions generated the report, and what cannot be claimed?

**Data:** quality_summary and overview_kpis, both disconnected. Other full-run summaries can be temporarily inspected for reconciliation.

- **Cards:** Data Source Label; Planning Assumptions (or use the text table if JSON is too long).
- **Metadata table:** quality_summary[check], [value], both Don't summarize. Keep `source`, `rows`, `kpis`, `planning`, `warnings`, `as_of`, `data_label` readable using word wrap. JSON values are strings; read them without inventing separate scalar fields.
- **Audit table:** overview_kpis[metric], [value] with value set to Don't summarize; disable totals because counts and volume have different units.
- **Slicer:** quality_summary[check] only, optional. No date/store/family slicers.
- **Text box:** explain synthetic data, volume not revenue, store/family/day grain, simulated inventory, assumed lead time and safety stock, descriptive promotions, unvalidated forecast baseline, and no real users or measured company outcomes.
- **Interpretation:** lets a reviewer trace scope and decide what evidence is sufficient for the analysis.
- **Caveat:** these are run metadata and outputs, not continuous monitoring or forecast confidence. Show the actual warnings and audit results rather than a generic status badge.

## 5. Manual acceptance checks before marking the report complete

Complete and record these checks in the finished report. The Python checks alone do not satisfy them.

1. **No filters, sample source:** Total Demand = 176,589.03; Average Daily Demand = 1,471.57525; Store Count = 3; Product Family Count = 4; Observed Days = 120; Promoted Demand = 44,173.11. Promotion Share ≈ 25.0146%. Historical dates are 2024-01-01 through 2024-04-29.
2. **Filter store 1:** Total Demand = 48,120.10 and Store Count = 1. Clear the filter, then select family GROCERY: Total Demand = 82,806.29 and Product Family Count = 1.
3. **Date filter:** select only 2024-01-01: Total Demand = 1,284.13, Observed Days = 1, Average Daily Demand = 1,284.13. No missing date is automatically zero-filled.
4. **Planning:** clear store/family/risk filters. There are 12 series: three each Reorder now, Monitor, Healthy, Overstock risk; Insufficient History = 0; Series Requiring Attention = 9. Snapshot As Of = 2024-04-29. A historical date selection must not change the snapshot. Selecting store 1 must reduce Planning Series Count to 4.
5. **Cross-check upstream:** compare no-filter family promotion means/lift with promotion_impact.csv. The DAX fraction times 100 must match lift_pct. Compare full-run bar totals to store_performance/family_performance. Do not add summaries to facts.
6. **Blank/edge behavior:** test a day/store/family with only one promotion group; lift must be blank. With a deliberately separate missing-promotion test source, Promoted Demand/lift must be unavailable, not invented values. Do not overwrite the normal sample exports for this optional test without regenerating afterward.
7. **Interactions:** test a bar selection, Clear selections, and synced slicers. Verify full-run reference tables and recommendation text remain labeled as such. Inspect Model view to confirm only five relationships, all Single.
8. **Refresh:** regenerate both pipeline and exports, press Home → Refresh, and recheck source/as-of and headline totals. Close and reopen the saved PBIX to confirm visuals and relationships persist. Copying a PBIX to another computer may require updating each CSV location under Data source settings → Change Source.
9. **Save verified report evidence:** File → Save As → `powerbi/StockPilot.pbix` within the project copy on your Windows machine. Copy that file back to the repository if needed. Capture the completed report pages and Model view into `powerbi/screenshots/`. The PBIX and screenshots are not ignored by the project rules.
10. **Update documentation only afterward:** change the README PBIX status and record the manual checks actually completed in docs/AUDIT.md. Mark the report as completed after the saved artifact and manual acceptance checks have been verified.

## 6. Refresh workflow and future production changes

Use a stable exports directory. After changing source/configuration: run the pipeline successfully → run the export script successfully → copy exports to the Windows location if different → Desktop Refresh → verify source, date and totals → save PBIX. Refresh alone does not execute Python, download public data, or create fresh forecasts. The Python database transaction does not make all CSV replacements atomic; rerun both commands after interruption.

For a real operating deployment, first confirm data ownership, units, reliable source refresh, actual stock/lead times, and forecast validation. A managed database connection and refresh process might eventually replace copied CSVs, but they are not implemented or needed for the current manual report.
