import argparse
from dataclasses import asdict
import json
from pathlib import Path
import duckdb
from .config import ROOT, PlanningConfig
from .data_loader import load_data
from .forecasting import forecast_demand
from .inventory import plan_inventory
from .metrics import kpis
from .recommendations import recommendations

def run_pipeline(source="auto", data_dir=None, output_dir=None, config=None):
    config = config or PlanningConfig()
    bronze, silver, selected, warnings = load_data(source, data_dir)
    output = Path(output_dir) if output_dir else ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    db_path = output / "stockpilot.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.execute("BEGIN")
        for schema in ("gold", "silver", "bronze"):
            con.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        for layer, tables in (("bronze", bronze), ("silver", silver)):
            con.execute((ROOT / f"sql/{layer}.sql").read_text())
            for name, frame in tables.items():
                con.register("input_frame", frame)
                con.execute(f"CREATE TABLE {layer}.{name} AS SELECT * FROM input_frame")
                con.unregister("input_frame")
        con.execute((ROOT / "sql/gold.sql").read_text())
        plan = plan_inventory(forecast_demand(silver["sales"], config), config, silver.get("inventory"))
        stores = con.sql("SELECT * FROM gold.store_performance").df()
        promos = con.sql("SELECT * FROM gold.promotion_impact").df()
        recs = recommendations(plan, stores, promos)
        for name, frame in (("reorder_risk", plan), ("recommendations", recs)):
            con.register("input_frame", frame)
            con.execute(f"CREATE TABLE gold.{name} AS SELECT * FROM input_frame")
            con.unregister("input_frame")
        if plan.coverage.lt(1).any():
            warnings.append("Some store/family series have incomplete trailing history; actionable reorder quantities are suppressed.")
        report = {"source": selected, "data_label": "Synthetic demo data" if selected == "sample" else "User-provided retail CSVs; provenance must be verified", "rows": len(silver["sales"]), "kpis": kpis(silver["sales"]), "planning": asdict(config), "warnings": warnings, "as_of": str(silver["sales"].date.max().date())}
        con.execute("CREATE TABLE gold.run_metadata (report_json VARCHAR)")
        con.execute("INSERT INTO gold.run_metadata VALUES (?)", [json.dumps(report)])
        con.execute("COMMIT")
        for name in ("daily_sales", "weekly_sales", "store_performance", "family_performance", "promotion_impact", "demand_volatility", "reorder_risk", "recommendations"):
            con.sql(f"SELECT * FROM gold.{name}").df().to_csv(output / f"{name}.csv", index=False)
        (output / "quality_report.json").write_text(json.dumps(report, indent=2))
        return report
    finally:
        con.close()

def main():
    parser = argparse.ArgumentParser(description="Build StockPilot analytics marts")
    parser.add_argument("--source", choices=["auto", "raw", "sample"], default="auto")
    parser.add_argument("--lead-time", type=int, default=7)
    parser.add_argument("--window", type=int, default=28)
    parser.add_argument("--review-days", type=int, default=7)
    parser.add_argument("--z-score", type=float, default=1.65)
    args = parser.parse_args()
    report = run_pipeline(args.source, config=PlanningConfig(args.window, args.lead_time, args.review_days, args.z_score))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
