import pandas as pd
import pytest
from stockpilot.validation import validate_sales, DataValidationError

def test_missing_required(sales):
    with pytest.raises(DataValidationError, match="Missing required"):
        validate_sales(sales.drop(columns="sales"))

@pytest.mark.parametrize("value", [-1, float("inf"), float("nan")])
def test_bad_sales(sales, value):
    sales.loc[0, "sales"] = value
    with pytest.raises(DataValidationError, match="sales"):
        validate_sales(sales)

def test_date_parsing(sales):
    sales["date"] = sales.date.dt.strftime("%Y-%m-%d")
    assert validate_sales(sales).date.iloc[0] == pd.Timestamp("2024-01-01")
    sales.loc[0, "date"] = "2024-02-30"
    with pytest.raises(DataValidationError, match="Invalid dates"):
        validate_sales(sales)

def test_duplicate_grain(sales):
    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_sales(pd.concat([sales, sales.iloc[[0]]]))

@pytest.mark.parametrize("column,value", [("family", "  "), ("store_nbr", None), ("onpromotion", -1)])
def test_missing_keys_and_negative_promotion(sales, column, value):
    sales.loc[0, column] = value
    with pytest.raises(DataValidationError):
        validate_sales(sales)
