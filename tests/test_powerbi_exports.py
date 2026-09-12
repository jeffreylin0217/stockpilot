import importlib.util
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "export_powerbi.py"

spec = importlib.util.spec_from_file_location("export_powerbi", SCRIPT_PATH)
powerbi_export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(powerbi_export)


def write_processed_outputs(processed: Path) -> None:
    pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-01"],
            "store_nbr": [1, 2],
            "family": ["A", "B"],
            "sales": [100.0, 200.0],
            "onpromotion": [0, 1],
            "promoted": [False, True],
            "weekday_number": [1, 1],
            "day_type": ["Weekday", "Weekday"],
        }
    ).to_csv(processed / "daily_sales.csv", index=False)

    pd.DataFrame(
        {
            "week": ["2024-01-01", "2024-01-01"],
            "store_nbr": [1, 2],
            "family": ["A", "B"],
            "sales": [100.0, 200.0],
            "observed_days": [1, 1],
        }
    ).to_csv(processed / "weekly_sales.csv", index=False)

    pd.DataFrame(
        {
            "family": ["A", "B"],
            "total_sales": [100.0, 200.0],
            "observed_days": [1, 1],
        }
    ).to_csv(processed / "family_performance.csv", index=False)

    pd.DataFrame(
        {
            "store_nbr": [1, 2],
            "total_sales": [100.0, 200.0],
            "observed_days": [1, 1],
            "average_daily_sales": [100.0, 200.0],
        }
    ).to_csv(processed / "store_performance.csv", index=False)

    pd.DataFrame(
        {
            "family": ["A", "B"],
            "promoted_average": [110.0, 210.0],
            "nonpromoted_average": [100.0, 200.0],
            "promoted_rows": [1, 1],
            "nonpromoted_rows": [1, 1],
            "lift_pct": [10.0, 5.0],
        }
    ).to_csv(processed / "promotion_impact.csv", index=False)

    pd.DataFrame(
        {
            "family": ["A", "B"],
            "daily_mean": [100.0, 200.0],
            "daily_std": [10.0, 20.0],
            "coefficient_of_variation": [0.1, 0.1],
        }
    ).to_csv(processed / "demand_volatility.csv", index=False)

    pd.DataFrame(
        {
            "store_nbr": [1, 2],
            "family": ["A", "B"],
            "risk": ["Reorder now", "Healthy"],
        }
    ).to_csv(processed / "reorder_risk.csv", index=False)

    pd.DataFrame(
        {
            "store_nbr": [1],
            "family": ["A"],
            "recommendation": ["Review replenishment"],
        }
    ).to_csv(processed / "recommendations.csv", index=False)

    with open(processed / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "sample",
                "data_label": "Synthetic demo data",
                "rows": 2,
            },
            f,
        )


def test_powerbi_exports_match_pipeline_schema(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    exports = tmp_path / "exports"
    processed.mkdir()

    write_processed_outputs(processed)

    monkeypatch.setattr(powerbi_export, "PROCESSED_DIR", processed)
    monkeypatch.setattr(powerbi_export, "EXPORT_DIR", exports)

    exported = powerbi_export.export_all()

    expected = {
        "daily_sales.csv",
        "weekly_sales.csv",
        "family_performance.csv",
        "store_performance.csv",
        "promotion_impact.csv",
        "demand_volatility.csv",
        "reorder_risk.csv",
        "recommendations.csv",
        "overview_kpis.csv",
        "quality_summary.csv",
    }

    assert {path.name for path in exported} == expected


def test_overview_kpis_use_demand_volume(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    exports = tmp_path / "exports"
    processed.mkdir()

    write_processed_outputs(processed)

    monkeypatch.setattr(powerbi_export, "PROCESSED_DIR", processed)
    monkeypatch.setattr(powerbi_export, "EXPORT_DIR", exports)

    powerbi_export.export_overview_kpis()

    df = pd.read_csv(exports / "overview_kpis.csv")
    values = dict(zip(df["metric"], df["value"]))

    assert values["Total demand volume"] == 300.0
    assert values["Product families"] == 2
    assert values["Stores"] == 2
    assert values["Reorder now series"] == 1

    assert "Total revenue" not in values
    assert "Total units sold" not in values
