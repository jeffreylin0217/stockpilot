import math
import pandas as pd
import pytest
from stockpilot.config import PlanningConfig
from stockpilot.forecasting import forecast_demand
from stockpilot.inventory import classify_risk, plan_inventory

@pytest.mark.parametrize("stock,expected", [(99, "Reorder now"), (100, "Monitor"), (110, "Monitor"), (111, "Healthy"), (300, "Healthy"), (301, "Overstock risk")])
def test_risk_boundaries(stock, expected):
    assert classify_risk(stock, 100, 200) == expected

def test_reorder_formula(sales):
    cfg = PlanningConfig(window_days=4)
    forecast = forecast_demand(sales, cfg)
    result = plan_inventory(forecast, cfg).iloc[0]
    expected = 22.5*7 + 1.65*sales.sales.std()*math.sqrt(7)
    assert result.reorder_point == pytest.approx(expected)
    assert result.reorder_quantity >= 0
    assert result.inventory_source == "Simulated scenario"

def test_missing_dates_suppress_actions(sales):
    cfg = PlanningConfig(window_days=4)
    result = plan_inventory(forecast_demand(sales.drop(index=1), cfg), cfg).iloc[0]
    assert result.coverage == 0.75
    assert result.risk == "Insufficient history"
    assert pd.isna(result.reorder_quantity)

def test_snapshot_date_and_zero_demand(sales):
    cfg = PlanningConfig(window_days=4)
    sales["sales"] = 0.0
    forecasts = forecast_demand(sales, cfg)
    actual = pd.DataFrame({"date": [pd.Timestamp("2024-01-04")], "store_nbr": [1], "family": ["A"], "inventory_on_hand": [100.]})
    result = plan_inventory(forecasts, cfg, actual).iloc[0]
    assert result.risk == "Overstock risk"
    assert pd.isna(result.days_of_supply)
    actual["date"] = pd.Timestamp("2024-01-03")
    assert plan_inventory(forecasts, cfg, actual).iloc[0].inventory_source == "Simulated scenario"

def test_window_uses_calendar_not_last_rows(sales):
    cfg = PlanningConfig(window_days=2)
    assert forecast_demand(sales, cfg).iloc[0].recent_average == 30

@pytest.mark.parametrize("kwargs", [{"lead_time_days":0}, {"window_days":-1}, {"window_days":1}, {"z_score":float("nan")}, {"review_days":1.5}])
def test_bad_configuration(kwargs):
    with pytest.raises(ValueError):
        PlanningConfig(**kwargs)
