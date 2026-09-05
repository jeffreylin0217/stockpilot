import math
import pandas as pd

def classify_risk(inventory, reorder_point, target_stock):
    if inventory < reorder_point:
        return "Reorder now"
    if inventory <= 1.1 * reorder_point:
        return "Monitor"
    if inventory > 1.5 * target_stock:
        return "Overstock risk"
    return "Healthy"

def plan_inventory(forecasts, config, actual=None):
    result = forecasts.copy()
    result["safety_stock"] = config.z_score * result.demand_std * math.sqrt(config.lead_time_days)
    result["reorder_point"] = result.expected_lead_time_demand + result.safety_stock
    result["target_stock_level"] = result.recent_average * (config.lead_time_days + config.review_days) + config.z_score * result.demand_std * math.sqrt(config.lead_time_days + config.review_days)
    # Four reproducible scenarios, not observed company stock.
    factors = [0.5, 1.05, 1.4, 4.0]
    result["inventory_on_hand"] = [row.reorder_point * factors[i % 4] for i, row in enumerate(result.itertuples())]
    result["inventory_source"] = "Simulated scenario"
    if actual is not None:
        # Only exact as-of snapshots are safe: stale inventory is not current stock.
        current = actual.loc[actual.date.eq(result.forecast_date.iloc[0])]
        result = result.merge(current[["store_nbr", "family", "inventory_on_hand"]].rename(columns={"inventory_on_hand":"actual_inventory"}), how="left", on=["store_nbr", "family"])
        mask = result.actual_inventory.notna()
        result.loc[mask, "inventory_on_hand"] = result.loc[mask, "actual_inventory"]
        result.loc[mask, "inventory_source"] = "Provided as-of snapshot (not independently verified)"
        result = result.drop(columns="actual_inventory")
    result["days_of_supply"] = result.inventory_on_hand / result.recent_average.where(result.recent_average.gt(0))
    result["reorder_quantity"] = (result.target_stock_level - result.inventory_on_hand).clip(lower=0)
    result["risk"] = [classify_risk(r.inventory_on_hand, r.reorder_point, r.target_stock_level) if r.coverage == 1 else "Insufficient history" for r in result.itertuples()]
    result.loc[result.coverage.lt(1), "reorder_quantity"] = float("nan")
    return result
