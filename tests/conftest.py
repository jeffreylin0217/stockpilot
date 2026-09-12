import pandas as pd
import pytest

@pytest.fixture
def sales():
    return pd.DataFrame({"date": pd.date_range("2024-01-01", periods=4), "store_nbr": [1]*4, "family": ["A"]*4, "sales": [10., 20., 20., 40.], "onpromotion": [0, 0, 1, 1]})
