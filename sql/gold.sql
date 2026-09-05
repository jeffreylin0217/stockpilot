CREATE SCHEMA gold;
CREATE TABLE gold.daily_sales AS
SELECT CAST(date AS DATE) AS date, store_nbr, family, sales, onpromotion,
       CASE WHEN onpromotion IS NULL THEN NULL ELSE onpromotion > 0 END AS promoted,
       isodow(date) AS weekday_number,
       CASE WHEN isodow(date) >= 6 THEN 'Weekend' ELSE 'Weekday' END AS day_type
FROM silver.sales;
CREATE TABLE gold.weekly_sales AS
SELECT CAST(date_trunc('week', date) AS DATE) AS week, store_nbr, family,
       sum(sales) AS sales, count(*) AS observed_days
FROM gold.daily_sales GROUP BY ALL;
CREATE TABLE gold.store_performance AS
SELECT store_nbr, sum(sales) AS total_sales, count(DISTINCT date) AS observed_days,
       sum(sales)/count(DISTINCT date) AS average_daily_sales
FROM gold.daily_sales GROUP BY store_nbr;
CREATE TABLE gold.family_performance AS
SELECT family, sum(sales) AS total_sales, count(DISTINCT date) AS observed_days
FROM gold.daily_sales GROUP BY family;
CREATE TABLE gold.promotion_impact AS
SELECT family,
 avg(sales) FILTER (WHERE promoted) AS promoted_average,
 avg(sales) FILTER (WHERE NOT promoted) AS nonpromoted_average,
 count(*) FILTER (WHERE promoted) AS promoted_rows,
 count(*) FILTER (WHERE NOT promoted) AS nonpromoted_rows,
 100*(avg(sales) FILTER (WHERE promoted)/nullif(avg(sales) FILTER (WHERE NOT promoted),0)-1) AS lift_pct
FROM gold.daily_sales GROUP BY family;
CREATE TABLE gold.demand_volatility AS
WITH daily AS (SELECT date, family, sum(sales) AS sales FROM gold.daily_sales GROUP BY ALL)
SELECT family, avg(sales) AS daily_mean, stddev_samp(sales) AS daily_std,
       stddev_samp(sales)/nullif(avg(sales),0) AS coefficient_of_variation
FROM daily GROUP BY family;
