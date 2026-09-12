# Interview guide

Use the demo version wording until you have actually run the public dataset. These scripts are starting points: explain the code in your own words and be ready to change a formula or query live.

## 30-second explanation
“I built StockPilot to practice retail demand and inventory analysis. It uses Python to validate daily sales records, DuckDB SQL to summarize demand, and Power BI-ready reporting datasets to analyze stores, product families and promotion patterns. I added an explainable moving-average forecast and reorder-point scenario. The included data and stock are synthetic, so I describe the results as planning demonstrations rather than business impact.”

## 60–90-second explanation
“The operations question is how to prioritize replenishment attention when demand varies across stores and categories. I built a pipeline with raw, cleaned and analytical tables. It checks dates, nonnegative sales and duplicate store-category-day records so the metrics aren't inflated. SQL calculates trends, rankings, promotion comparisons and variability. Then Python uses a trailing 28-day average to estimate demand during a configurable lead time and adds safety stock based on daily variability. The reporting layer lets someone inspect the demand evidence and see why a scenario is flagged. Missing dates are not silently treated as zero, and incomplete history suppresses actionable order quantities. Because the included data is synthetic and category-level, I haven't claimed actual stockout reductions or forecast accuracy. My next step would be running the public dataset and testing forecasts on later dates before adding complexity.”

## Technical walkthrough
1. Show `data/sample/README.md` and one row of `train.csv`. State the grain.
2. Run the pipeline and read its source label and warning list.
3. Open `validation.py`: explain why duplicates would double count sales.
4. Open `sql/gold.sql`: explain GROUP BY and the two conditional promotion means.
5. Walk through `forecasting.py`: latest global date, calendar window, observed-day coverage.
6. Explain one row of `reorder_risk.csv`, including its simulated inventory source.
7. Inspect the daily-demand and reorder-risk reporting outputs and distinguish historical analysis from the latest planning snapshot.
8. Run pytest and explain one expected numerical result rather than only citing a test count.

## Business walkthrough
Start with the highest-volume categories and stores to decide where review time matters most. Compare average demand by weekday/weekend without confusing raw totals with unequal day counts. Review variability before assuming a stable replenishment cadence. Treat weak promotion lift as a reason to investigate timing and margin, not cancel promotions automatically. Check inventory provenance and lead time before acting on a reorder flag. Recommendations are attention priorities, not purchase instructions.

## Likely questions and plain answers
**What is DuckDB?** An embedded analytical database. I can query local tables with SQL without running a database server. The output is one local file.

**Why Bronze/Silver/Gold?** They separate what I loaded, what passed validation, and what is ready for analysis. It makes errors easier to trace without requiring a complex platform.

**What is the forecast?** The average daily sales over the last 28 calendar days for each store/category. The lead-time forecast multiplies that average by lead-time days. I haven't claimed it beats a seasonal baseline.

**Why not machine learning?** I wanted a baseline that is easy to explain and audit. First I'd measure holdout error and understand seasonality; complexity should earn its place.

**What is a reorder point?** The inventory threshold covering expected demand while replenishment arrives plus a buffer for variability.

**What is safety stock?** A buffer for uncertain demand. With independent daily demand, lead-time standard deviation grows with the square root of lead time. I multiply it by an assumed z value. Real demand and lead time may violate those assumptions.

**Can you calculate an example?** At mean 10/day, std 2/day, 7-day lead time and z=1.65, expected demand is 70 and safety stock is about 8.73. Reorder point is about 78.73. Stock of 60 is below that point. The target also covers the review period.

**What is promotion lift?** If promoted rows average 30 and nonpromoted rows average 15, lift is 100%. It doesn't establish that promotions caused the difference. Category rows may include unpromoted items.

**Did you improve a real retailer's operations?** No. This version demonstrates an analytical workflow using synthetic data and explicit planning assumptions. I would need measured evidence and authorization to claim business use.

**What if a date is missing?** I leave it unknown, report incomplete coverage and suppress actionable reorder quantities. Zero sales is a valid observation and has a different meaning.

**Why don't you join transactions to every sales row and sum them?** Store-day transactions would repeat once per category and become overcounted. I retain context tables separately until a grain-safe question requires a join.

**What did tests catch or protect against?** Incorrect denominators, invalid sales, duplicate grains, boundary classification mistakes, stale inventory snapshots and Power BI export regressions.

**What would you improve?** Measure rolling-origin forecast accuracy, then evaluate same-weekday forecasts, promotion adjustments, SKU stock and realistic replenishment simulation. I would document accuracy and operational assumptions before claiming value.

**How did you build it?** Explain the assistance and tools you actually used, including AI assistance if asked. Don't claim to have independently authored code you cannot explain. Practice implementing a small change and checking it with a test.
