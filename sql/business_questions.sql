-- Run against data/processed/stockpilot.duckdb after the pipeline.
-- These SELECT-only queries illustrate analysis; the pipeline does not execute this file.
-- Results reflect whichever source was last loaded. Sales is volume, never revenue.

-- 1. Which stores account for demand? Compare observed-day coverage as well as volume.
SELECT store_nbr, observed_days, round(total_sales, 2) AS demand_volume,
       round(average_daily_sales, 2) AS average_daily_demand,
       round(100.0 * total_sales / nullif(sum(total_sales) OVER (), 0), 1) AS volume_share_pct
FROM gold.store_performance
ORDER BY total_sales DESC;

-- 2. Is promotion-associated demand higher within a store AND family?
-- Stratifying by store reduces store-mix confounding; time/seasonality remain uncontrolled.
-- A minimum of 5 rows per group is a review heuristic, not a significance test.
WITH comparisons AS (
    SELECT store_nbr, family,
           count(*) FILTER (WHERE promoted) AS promoted_rows,
           count(*) FILTER (WHERE NOT promoted) AS nonpromoted_rows,
           avg(sales) FILTER (WHERE promoted) AS promoted_mean,
           avg(sales) FILTER (WHERE NOT promoted) AS nonpromoted_mean
    FROM gold.daily_sales
    GROUP BY store_nbr, family
)
SELECT *, round(100.0 * (promoted_mean / nullif(nonpromoted_mean, 0) - 1), 1)
          AS descriptive_difference_pct
FROM comparisons
WHERE promoted_rows >= 5 AND nonpromoted_rows >= 5
ORDER BY family, store_nbr;

-- 3. Which families have greater variability relative to their own mean?
-- Daily totals are across stores. CV is undefined when mean demand is zero.
SELECT family, round(daily_mean, 2) AS average_daily_demand,
       round(daily_std, 2) AS daily_standard_deviation,
       round(coefficient_of_variation, 3) AS cv
FROM gold.demand_volatility
ORDER BY coefficient_of_variation DESC NULLS LAST;

-- 4. What belongs in the replenishment review queue?
-- Preserve inventory_source: simulated scenarios must never look like actual stock.
-- Includes missing-history cases for data review; not an executable purchase order.
SELECT store_nbr, family, forecast_date, inventory_source, coverage, risk,
       round(inventory_on_hand, 1) AS stock,
       round(reorder_point, 1) AS reorder_point,
       round(reorder_quantity, 1) AS scenario_quantity
FROM gold.reorder_risk
WHERE risk <> 'Healthy'
ORDER BY CASE risk WHEN 'Insufficient history' THEN 1 WHEN 'Reorder now' THEN 2
                   WHEN 'Monitor' THEN 3 ELSE 4 END, store_nbr, family;
