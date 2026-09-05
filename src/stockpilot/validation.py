"""Reject invalid required data. Optional files are validated separately."""
import numpy as np
import pandas as pd

class DataValidationError(ValueError):
    pass

def clean_table(frame, required, keys, numeric=(), dates=()):
    missing = set(required) - set(frame.columns)
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(sorted(missing))}")
    df = frame.copy()
    if df.empty:
        raise DataValidationError("Table has no rows")
    for col in keys:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
            raise DataValidationError(f"Missing {col} values")
    for col in dates:
        parsed = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
        if parsed.isna().any():
            raise DataValidationError(f"Invalid dates in {col}; use YYYY-MM-DD")
        df[col] = parsed
    for col in numeric:
        values = pd.to_numeric(df[col], errors="coerce")
        if values.isna().any() or not np.isfinite(values).all() or (values < 0).any():
            raise DataValidationError(f"{col} must contain finite nonnegative numbers")
        df[col] = values
    if "store_nbr" in df:
        values = pd.to_numeric(df.store_nbr, errors="coerce")
        if values.isna().any() or not np.isfinite(values).all() or (values <= 0).any() or (values % 1 != 0).any():
            raise DataValidationError("store_nbr must contain positive integers")
        df["store_nbr"] = values.astype(int)
    if "family" in df:
        df["family"] = df.family.astype(str).str.strip()
    if keys and df.duplicated(list(keys)).any():
        raise DataValidationError(f"Duplicate rows at grain {', '.join(keys)}")
    return df

def validate_sales(frame):
    required = ("date", "store_nbr", "family", "sales")
    numeric = ["sales"] + (["onpromotion"] if "onpromotion" in frame else [])
    return clean_table(frame, required, ("date", "store_nbr", "family"), numeric, ("date",))
