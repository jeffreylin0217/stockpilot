import pandas as pd
import pytest
from stockpilot.metrics import kpis, promotion_impact

def test_kpis(sales):
    result = kpis(sales)
    assert result["total_sales"] == 90
    assert result["average_daily_sales"] == 22.5
    assert result["stores"] == result["families"] == 1
    assert result["promoted_sales"] == 60

def test_promotion_lift(sales):
    result = promotion_impact(sales).iloc[0]
    assert result.lift_pct == pytest.approx(100)
    assert result.promoted_rows == 2

def test_undefined_promotion(sales):
    sales["onpromotion"] = 1
    assert pd.isna(promotion_impact(sales).iloc[0].lift_pct)
    sales["onpromotion"] = float("nan")
    assert kpis(sales)["promoted_sales"] is None
