import pandas as pd

def kpis(df):
    days = df.date.nunique()
    known = df.onpromotion.notna() if "onpromotion" in df else pd.Series(False, index=df.index)
    return {"total_sales": float(df.sales.sum()),
            "average_daily_sales": float(df.sales.sum() / days) if days else 0,
            "stores": int(df.store_nbr.nunique()), "families": int(df.family.nunique()),
            "start": str(df.date.min())[:10] if days else None,
            "end": str(df.date.max())[:10] if days else None,
            "promoted_sales": float(df.loc[df.onpromotion.gt(0), "sales"].sum()) if known.any() else None}

def promotion_impact(df):
    rows = []
    for family, group in df.groupby("family"):
        promo = group.loc[group.onpromotion.gt(0), "sales"]
        base = group.loc[group.onpromotion.eq(0), "sales"]
        rows.append({"family": family, "promoted_average": promo.mean(),
                     "nonpromoted_average": base.mean(), "promoted_rows": len(promo),
                     "nonpromoted_rows": len(base),
                     "lift_pct": 100 * (promo.mean()/base.mean()-1) if len(promo) and len(base) and base.mean() > 0 else float("nan")})
    return pd.DataFrame(rows)
