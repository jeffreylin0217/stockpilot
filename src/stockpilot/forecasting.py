from datetime import timedelta
import pandas as pd

def forecast_demand(sales, config):
    """Calendar window; absent dates remain unknown, never silently zero-filled."""
    end = pd.Timestamp(sales.date.max())
    start = pd.Timestamp(end.to_pydatetime() - timedelta(days=config.window_days - 1))
    recent = sales.loc[sales.date.between(start, end)]
    keys = sales[["store_nbr", "family"]].drop_duplicates().sort_values(["store_nbr", "family"])
    stats = recent.groupby(["store_nbr", "family"]).agg(
        recent_average=("sales", "mean"), demand_std=("sales", "std"),
        observed_days=("date", "nunique"), last_observed_date=("date", "max")).reset_index()
    out = keys.merge(stats, how="left", on=["store_nbr", "family"])
    out["observed_days"] = out.observed_days.fillna(0).astype(int)
    out["coverage"] = out.observed_days / config.window_days
    out["forecast_date"] = end
    out["expected_lead_time_demand"] = out.recent_average * config.lead_time_days
    out["forecast_quality"] = out.coverage.map(lambda x: "Full window" if x == 1 else "Incomplete history")
    return out
