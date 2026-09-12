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
            "scope": ["Store 1 / A"],
            "evidence": ["Simulated inventory below reorder point"],
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


def _export_real_sample(tmp_path, monkeypatch):
    from stockpilot.pipeline import run_pipeline

    processed, exports = tmp_path / "processed", tmp_path / "exports"
    report = run_pipeline("sample", output_dir=processed)
    monkeypatch.setattr(powerbi_export, "PROCESSED_DIR", processed)
    monkeypatch.setattr(powerbi_export, "EXPORT_DIR", exports)
    paths = powerbi_export.export_all()
    return {p.stem: pd.read_csv(p) for p in paths}, report


def test_real_pipeline_exports_have_model_keys_and_valid_numbers(tmp_path, monkeypatch):
    """Check actual pipeline files, not only hand-authored export fixtures."""
    import numpy as np

    tables, _ = _export_real_sample(tmp_path, monkeypatch)
    expected = {
        "daily_sales": {"date", "store_nbr", "family", "sales", "onpromotion", "promoted", "weekday_number", "day_type"},
        "weekly_sales": {"week", "store_nbr", "family", "sales", "observed_days"},
        "store_performance": {"store_nbr", "total_sales", "observed_days", "average_daily_sales"},
        "family_performance": {"family", "total_sales", "observed_days"},
        "promotion_impact": {"family", "promoted_average", "nonpromoted_average", "promoted_rows", "nonpromoted_rows", "lift_pct"},
        "demand_volatility": {"family", "daily_mean", "daily_std", "coefficient_of_variation"},
        "reorder_risk": {"store_nbr", "family", "recent_average", "demand_std", "observed_days", "last_observed_date", "coverage", "forecast_date", "expected_lead_time_demand", "forecast_quality", "safety_stock", "reorder_point", "target_stock_level", "inventory_on_hand", "inventory_source", "days_of_supply", "reorder_quantity", "risk"},
        "recommendations": {"scope", "evidence", "recommendation"},
        "overview_kpis": {"metric", "value"},
        "quality_summary": {"check", "value"},
    }
    assert set(tables) == set(expected)
    for name, columns in expected.items():
        assert columns.issubset(tables[name].columns), name
        assert not tables[name].empty, name  # This particular demo produces recommendations.
    for name, keys in {"daily_sales": ["date", "store_nbr", "family"],
                       "weekly_sales": ["week", "store_nbr", "family"],
                       "reorder_risk": ["store_nbr", "family"],
                       "store_performance": ["store_nbr"], "family_performance": ["family"],
                       "quality_summary": ["check"], "overview_kpis": ["metric"]}.items():
        assert not tables[name][keys].isna().any().any()
        assert not tables[name].duplicated(keys).any(), name
    for name, columns in {"daily_sales": ["sales", "onpromotion"],
                          "reorder_risk": ["recent_average", "demand_std", "coverage", "safety_stock", "reorder_point", "target_stock_level", "inventory_on_hand", "days_of_supply", "reorder_quantity"]}.items():
        values = tables[name][columns].apply(pd.to_numeric, errors="raise")
        assert values.notna().all().all()  # Demo has complete histories and positive means.
        assert np.isfinite(values.to_numpy()).all()
        assert values.ge(0).all().all()
    assert tables["reorder_risk"].coverage.le(1).all()
    assert pd.to_datetime(tables["daily_sales"].date, errors="raise").notna().all()
    assert set(tables["reorder_risk"].store_nbr) <= set(tables["daily_sales"].store_nbr)
    assert set(tables["reorder_risk"].family) <= set(tables["daily_sales"].family)


def test_reporting_totals_and_promotion_groups_reconcile(tmp_path, monkeypatch):
    import pytest

    tables, report = _export_real_sample(tmp_path, monkeypatch)
    daily = tables["daily_sales"]
    total = daily.sales.sum()
    assert total == pytest.approx(report["kpis"]["total_sales"])
    for name, column in [("weekly_sales", "sales"), ("family_performance", "total_sales"), ("store_performance", "total_sales")]:
        assert tables[name][column].sum() == pytest.approx(total)
    # Verify the whole period and a specific dimension member, avoiding sum-only false positives.
    for r in tables["store_performance"].itertuples():
        part = daily[daily.store_nbr.eq(r.store_nbr)]
        assert r.total_sales == pytest.approx(part.sales.sum())
        assert r.average_daily_sales == pytest.approx(part.sales.sum()/part.date.nunique())
    for r in tables["promotion_impact"].itertuples():
        part = daily[daily.family.eq(r.family)]
        promoted = part.loc[part.onpromotion.gt(0), "sales"]
        baseline = part.loc[part.onpromotion.eq(0), "sales"]
        assert r.promoted_rows == len(promoted)
        assert r.nonpromoted_rows == len(baseline)
        assert r.lift_pct == pytest.approx(100*(promoted.mean()/baseline.mean()-1))
    overview = tables["overview_kpis"].set_index("metric").value
    assert overview["Total demand volume"] == pytest.approx(total, abs=0.005)
    assert overview["Reorder now series"] == tables["reorder_risk"].risk.eq("Reorder now").sum()
    quality = tables["quality_summary"].set_index("check").value
    assert quality["data_label"] == "Synthetic demo data"
    assert int(quality["rows"]) == len(daily)
    assert json.loads(quality["planning"]) == report["planning"]


def test_exports_preserve_unknown_promotion_and_incomplete_planning(tmp_path, monkeypatch, sales):
    """Blank comparison/quantity values must not become misleading zero metrics."""
    from stockpilot.pipeline import run_pipeline

    raw = tmp_path / "raw"
    raw.mkdir()
    sales.drop(columns="onpromotion").to_csv(raw / "train.csv", index=False)
    processed, exports = tmp_path / "processed", tmp_path / "exports"
    run_pipeline("raw", data_dir=tmp_path, output_dir=processed)
    monkeypatch.setattr(powerbi_export, "PROCESSED_DIR", processed)
    monkeypatch.setattr(powerbi_export, "EXPORT_DIR", exports)
    powerbi_export.export_all()
    daily = pd.read_csv(exports / "daily_sales.csv")
    promotion = pd.read_csv(exports / "promotion_impact.csv")
    plan = pd.read_csv(exports / "reorder_risk.csv")
    assert daily.onpromotion.isna().all() and daily.promoted.isna().all()
    assert promotion.lift_pct.isna().all()
    assert promotion.promoted_average.isna().all() and promotion.nonpromoted_average.isna().all()
    assert plan.risk.eq("Insufficient history").all()
    assert plan.reorder_quantity.isna().all()
