from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
EXPORT_DIR = ROOT / "powerbi" / "exports"

EXPECTED_EXPORTS = {
    "daily_sales.csv": "daily_sales.csv",
    "weekly_sales.csv": "weekly_sales.csv",
    "family_performance.csv": "family_performance.csv",
    "store_performance.csv": "store_performance.csv",
    "promotion_impact.csv": "promotion_impact.csv",
    "demand_volatility.csv": "demand_volatility.csv",
    "reorder_risk.csv": "reorder_risk.csv",
    "recommendations.csv": "recommendations.csv",
}


def _read_csv(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the StockPilot pipeline first."
        )
    return pd.read_csv(path)


def _write_csv(df: pd.DataFrame, name: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / name
    df.to_csv(out, index=False)
    return out


def export_overview_kpis() -> Path:
    family = _read_csv("family_performance.csv")
    stores = _read_csv("store_performance.csv")
    reorder = _read_csv("reorder_risk.csv")

    total_demand = float(family["total_sales"].sum())
    family_count = int(family["family"].nunique())
    store_count = int(stores["store_nbr"].nunique())

    reorder_now = 0
    if "risk" in reorder.columns:
        reorder_now = int(
            reorder["risk"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("reorder now")
            .sum()
        )

    df = pd.DataFrame(
        [
            {"metric": "Total demand volume", "value": round(total_demand, 2)},
            {"metric": "Product families", "value": family_count},
            {"metric": "Stores", "value": store_count},
            {"metric": "Reorder now series", "value": reorder_now},
        ]
    )

    return _write_csv(df, "overview_kpis.csv")


def export_quality_summary() -> Path:
    path = PROCESSED_DIR / "quality_report.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the StockPilot pipeline first."
        )

    report = json.loads(path.read_text())

    rows = []
    for key, value in report.items():
        rows.append(
            {
                "check": key,
                "value": json.dumps(value) if isinstance(value, (dict, list)) else value,
            }
        )

    return _write_csv(pd.DataFrame(rows), "quality_summary.csv")


def export_processed_csvs() -> list[Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    exported = []

    for source_name, export_name in EXPECTED_EXPORTS.items():
        source = PROCESSED_DIR / source_name

        if not source.exists():
            raise FileNotFoundError(
                f"Missing {source}. Run the StockPilot pipeline first."
            )

        destination = EXPORT_DIR / export_name
        shutil.copyfile(source, destination)
        exported.append(destination)

    return exported


def export_all() -> list[Path]:
    exported = export_processed_csvs()
    exported.append(export_overview_kpis())
    exported.append(export_quality_summary())
    return exported


def main() -> None:
    exported = export_all()

    print("Power BI export complete.")

    for path in exported:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
