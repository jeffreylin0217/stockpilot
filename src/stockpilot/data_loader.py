from pathlib import Path
import pandas as pd
from .config import ROOT
from .validation import clean_table, validate_sales, DataValidationError

OPTIONAL = {
    "stores": (("store_nbr",), ("store_nbr",), (), ()),
    "transactions": (("date", "store_nbr", "transactions"), ("date", "store_nbr"), ("transactions",), ("date",)),
    "oil": (("date", "dcoilwtico"), ("date",), (), ("date",)),
    "holidays_events": (("date", "type", "locale", "locale_name", "description", "transferred"), (), (), ("date",)),
    "inventory": (("date", "store_nbr", "family", "inventory_on_hand"), ("date", "store_nbr", "family"), ("inventory_on_hand",), ("date",)),
}

def load_data(source="auto", data_dir=None):
    base = Path(data_dir) if data_dir else ROOT / "data"
    selected = ("raw" if (base / "raw/train.csv").exists() else "sample") if source == "auto" else source
    if selected not in ("raw", "sample"):
        raise ValueError("source must be auto, raw, or sample")
    directory = base / selected
    path = directory / "train.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Place Kaggle CSVs in data/raw or use --source sample.")
    bronze = {"sales": pd.read_csv(path)}
    silver = {"sales": validate_sales(bronze["sales"])}
    warnings = []
    if "onpromotion" not in silver["sales"]:
        silver["sales"]["onpromotion"] = float("nan")
        warnings.append("onpromotion absent: promotion analysis unavailable.")
    for name, spec in OPTIONAL.items():
        file = directory / f"{name}.csv"
        if not file.exists():
            warnings.append(f"Optional {name}.csv absent.")
            continue
        try:
            bronze[name] = pd.read_csv(file)
            silver[name] = clean_table(bronze[name], *spec)
            if name == "oil":
                silver[name]["dcoilwtico"] = pd.to_numeric(silver[name].dcoilwtico, errors="coerce")
                warnings.append("Oil retained as context; missing oil prices are allowed; no causal model uses oil.")
        except (DataValidationError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            warnings.append(f"Ignored optional {name}: {exc}")
    return bronze, silver, selected, warnings
