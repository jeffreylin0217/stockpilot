# Learning StockPilot

Work through these exercises until you can explain the project without reading a script.

1. **Operations problem.** Explain why high average demand and high variability create different planning concerns. Find a category in the demo and give a conservative review recommendation.
2. **Dataset.** Read five CSV rows. Identify date/store/family grain, demand volume and promotion count. Explain why the demo is synthetic and why sales is not revenue or uncensored customer demand.
3. **SQL.** Run `SELECT family, SUM(sales) FROM gold.daily_sales GROUP BY family;` using a DuckDB Python connection. Add a store filter. Explain why WHERE runs before aggregation and why NULLIF prevents division by zero.
4. **DuckDB.** Open the generated `.duckdb` file in Python with `duckdb.connect(...)`. Query a Gold table, then close the connection. Explain why a local embedded database fits this project.
5. **pandas.** Practice `read_csv`, `to_datetime`, boolean filtering, `groupby`, `agg` and `merge`. Predict the row count before joining a store-day table to family-day observations.
6. **KPIs.** On values 10, 20, 20, 40 across four days, compute total 90 and daily average 22.5. Explain why multiple store/category rows make an average of rows different from average total daily sales.
7. **Inventory formulas.** For demand 10/day, std 2, lead 7, z 1.65, calculate safety stock 8.73 and reorder point 78.73. With a 7-day review period, target is about 152.35. At stock 60, suggested scenario quantity is about 92.35. Explain the independence assumption behind square-root scaling.
8. **Promotion lift.** Compute `(30/15 - 1)*100 = 100%`. Explain missing groups, zero denominator, category mixtures and confounding by seasonality or store mix.
9. **Forecast baseline.** Change the window from 28 to 14 and inspect how recent demand changes. Explain why this is not an accuracy test. Sketch a chronological holdout that fits only on earlier dates and evaluates later dates.
10. **Power BI reporting connection.** Trace CSV → validation → SQL → planning → processed CSV → Power BI export. Explain which datasets support demand trends, performance analysis and replenishment reporting.
11. **Honest limitations.** State three: synthetic stock, no causal promotion estimate, no measured forecast accuracy. Then propose the specific evidence needed to overcome each.
12. **Code quality.** Run pytest, read a failing assertion if you deliberately change a formula, then restore it. Add a small useful metric and its known-answer test. Understand configuration, pure functions, source labels, optional-file warnings and transaction boundaries. Never commit credentials or downloaded private data.

## Practice interview exercise
Run the sample pipeline, choose one store/category, and spend five minutes explaining its demand history, forecast, variability, inventory provenance, risk classification and a recommendation. End with what additional data would change your decision. Ask a friend to challenge the assumptions.

## Suggested next independent improvement
Add a chronological baseline evaluation module: reserve the last 14 days, fit a trailing-28-day mean only before the cutoff, predict the holdout, and calculate MAE. Compare a same-weekday baseline using identical dates. Save the split, predictions and metric; do not tune on the final holdout. This work is a next step, not something the current implementation claims to have done.
