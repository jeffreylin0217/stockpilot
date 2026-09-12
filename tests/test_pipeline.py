import duckdb
import pandas as pd
import pytest
from stockpilot.pipeline import run_pipeline
from stockpilot.config import ROOT
from stockpilot.validation import DataValidationError

def test_sample_pipeline_and_rerun(tmp_path):
    report = run_pipeline("sample", output_dir=tmp_path)
    assert report["rows"] == 1440
    assert report["data_label"] == "Synthetic demo data"
    with duckdb.connect(str(tmp_path / "stockpilot.duckdb")) as con:
        assert con.sql("SELECT count(*) FROM gold.reorder_risk").fetchone()[0] == 12
        assert con.sql("SELECT sum(sales) FROM gold.daily_sales").fetchone()[0] == pytest.approx(report["kpis"]["total_sales"])
        assert con.sql("SELECT sum(sales) FROM gold.weekly_sales").fetchone()[0] == pytest.approx(report["kpis"]["total_sales"])
        assert con.sql("SELECT count(*) FROM gold.recommendations").fetchone()[0] > 0
    assert run_pipeline("sample", output_dir=tmp_path)["rows"] == 1440

def test_raw_optional_files_and_sql_promotion(tmp_path, sales):
    raw = tmp_path / "raw"
    raw.mkdir()
    sales.to_csv(raw / "train.csv", index=False)
    (raw / "stores.csv").write_text("unexpected\n1\n")
    report = run_pipeline("auto", data_dir=tmp_path, output_dir=tmp_path / "out")
    assert report["source"] == "raw"
    assert any("Ignored optional stores" in x for x in report["warnings"])
    with duckdb.connect(str(tmp_path / "out/stockpilot.duckdb")) as con:
        assert con.sql("SELECT lift_pct FROM gold.promotion_impact").fetchone()[0] == pytest.approx(100)
    sales.drop(columns="onpromotion").to_csv(raw / "train.csv", index=False)
    report = run_pipeline("raw", data_dir=tmp_path, output_dir=tmp_path / "out")
    assert report["kpis"]["promoted_sales"] is None
    sales.loc[0, "sales"] = -1
    sales.to_csv(raw / "train.csv", index=False)
    with pytest.raises(DataValidationError):
        run_pipeline("auto", data_dir=tmp_path, output_dir=tmp_path / "out")
    with duckdb.connect(str(tmp_path / "out/stockpilot.duckdb")) as con:
        assert con.sql("SELECT sum(sales) FROM gold.daily_sales").fetchone()[0] == 90
