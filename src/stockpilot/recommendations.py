import pandas as pd

def recommendations(plan, stores, promotions):
    rows = []
    for r in plan.itertuples():
        if r.risk == "Reorder now":
            rows.append({"scope": f"Store {r.store_nbr} / {r.family}", "evidence": f"{r.inventory_source}; stock {r.inventory_on_hand:.1f} < reorder point {r.reorder_point:.1f}", "recommendation": "Review replenishment under these planning assumptions; this is not an observed stockout."})
        elif r.recent_average > 0 and r.demand_std / r.recent_average > 0.5:
            rows.append({"scope": f"Store {r.store_nbr} / {r.family}", "evidence": "Recent daily coefficient of variation exceeds 0.5", "recommendation": "Monitor variability and investigate demand spikes before changing safety stock."})
    if not stores.empty:
        r = stores.sort_values("total_sales", ascending=False).iloc[0]
        rows.append({"scope": f"Store {int(r.store_nbr)}", "evidence": f"Highest observed sales volume: {r.total_sales:,.1f}", "recommendation": "Prioritize replenishment review; volume alone does not establish profitability or persistent performance."})
    for r in promotions.itertuples():
        if pd.notna(r.lift_pct) and r.lift_pct <= 0 and min(r.promoted_rows, r.nonpromoted_rows) >= 5:
            rows.append({"scope": r.family, "evidence": f"Observed promotion lift {r.lift_pct:.1f}%", "recommendation": "Review promotion timing, store mix and margin before deciding whether to continue promotions."})
    return pd.DataFrame(rows, columns=["scope", "evidence", "recommendation"])
