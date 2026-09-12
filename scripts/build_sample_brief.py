"""Regenerate the GitHub preview and findings from the included synthetic sample.

Runs the existing pipeline in a temporary directory; never overwrites a user's
processed data or Power BI exports. Requires requirements-visuals.txt.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd

from stockpilot.config import ROOT
from stockpilot.pipeline import run_pipeline


def build_brief():
    with TemporaryDirectory(prefix="stockpilot-preview-") as directory:
        report = run_pipeline("sample", output_dir=directory)
        output = Path(directory)
        daily = pd.read_csv(output / "daily_sales.csv", parse_dates=["date"])
        stores = pd.read_csv(output / "store_performance.csv").sort_values("store_nbr")
        promotions = pd.read_csv(output / "promotion_impact.csv").sort_values("lift_pct")
        volatility = pd.read_csv(output / "demand_volatility.csv")
        plan = pd.read_csv(output / "reorder_risk.csv")

    # Index each family's weekly daily mean to its first complete week = 100.
    # Only use weeks with all 7 dates at every store/family: no partial-week bias.
    daily["week"] = daily.date - pd.to_timedelta(daily.date.dt.dayofweek, unit="D")
    weekly = daily.groupby(["week", "store_nbr", "family"]).agg(
        volume=("sales", "sum"), days=("date", "nunique")
    ).reset_index()
    expected_series = len(plan)
    coverage = weekly.groupby("week").agg(series=("days", "size"), min_days=("days", "min"))
    complete = coverage.index[(coverage.series == expected_series) & (coverage.min_days == 7)]
    weekly_family = weekly[weekly.week.isin(complete)].groupby(["week", "family"]).volume.sum().unstack()
    indexed = weekly_family.div(weekly_family.iloc[0]).mul(100)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.8), gridspec_kw={"width_ratios": [1.45, 1, 1]})
    fig.patch.set_facecolor("#f7fafc")
    fig.suptitle("StockPilot | Retail planning review", x=.055, ha="left", y=.97,
                 fontsize=22, weight="bold", color="#16324f")
    fig.text(.055, .87, "SYNTHETIC DEMO  •  3 stores  /  4 families  /  120 days  •  Jan–Apr 2024",
             fontsize=11, color="#465b70")
    colors = ["#167d9a", "#16324f", "#a56b20", "#9172b6"]
    for family, color in zip(indexed.columns, colors):
        axes[0].plot(indexed.index, indexed[family], label=family.title(), color=color, linewidth=1.8)
    axes[0].axhline(100, color="#a0aab4", linestyle="--", linewidth=.8)
    axes[0].set_title("How does demand change?", loc="left", weight="bold", pad=15)
    axes[0].set_ylabel("Weekly volume index (first full week = 100)")
    ticks = indexed.index[::4]
    axes[0].set_xticks(ticks, ticks.strftime("%b %d"))
    axes[0].legend(loc="upper left", ncol=2, fontsize=8, frameon=False)

    bars = axes[1].barh(promotions.family.str.title(), promotions.lift_pct,
                        color=["#b26443" if x < 0 else "#167d9a" for x in promotions.lift_pct])
    axes[1].bar_label(bars, labels=[f"{x:+.1f}%" for x in promotions.lift_pct], padding=4, fontsize=9)
    axes[1].axvline(0, color="#a0aab4", linewidth=.8)
    axes[1].set_xlim(-22, 43)
    axes[1].xaxis.set_major_formatter(PercentFormatter(100))
    axes[1].set_title("Are promotions associated\nwith higher demand?", loc="left", weight="bold", pad=15)
    axes[1].set_xlabel("Promoted vs nonpromoted row mean")

    order = ["Reorder now", "Monitor", "Healthy", "Overstock risk"]
    counts = plan.risk.value_counts().reindex(order, fill_value=0)
    if counts.sum() != len(plan):
        raise ValueError("Preview risk categories do not cover all planning rows")
    bars = axes[2].barh(counts.index, counts, color=["#b26443", "#a56b20", "#167d9a", "#9172b6"])
    axes[2].bar_label(bars, padding=4)
    axes[2].invert_yaxis()
    axes[2].set_xlim(0, max(counts) + 1)
    axes[2].set_xticks(range(int(max(counts)) + 1))
    axes[2].set_title("Which scenarios need review?", loc="left", weight="bold", pad=15)
    axes[2].set_xlabel("Store / family series")
    for ax in axes:
        ax.set_facecolor("#f7fafc")
        ax.tick_params(length=0, pad=7)
    fig.subplots_adjust(left=.055, right=.965, top=.72, bottom=.24, wspace=.65)
    fig.text(.055, .12, "Complete weeks only in trend chart. Promotion comparisons are descriptive, not causal.", color="#465b70", fontsize=10)
    fig.text(.055, .065, "Inventory is deliberately simulated; equal risk counts are constructed scenarios. Python preview, not a Power BI screenshot.", color="#465b70", fontsize=10)
    image_path = ROOT / "docs/images/sample-analysis.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(image_path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    highest = stores.loc[stores.total_sales.idxmax()]
    most_variable = volatility.loc[volatility.coefficient_of_variation.idxmax()]
    total = report["kpis"]["total_sales"]
    text = f"""# Sample business review

Generated from the included **synthetic sample**, {report['kpis']['start']} through {report['kpis']['end']}. Reproduce with `python scripts/build_sample_brief.py` after installing `requirements-visuals.txt`. The script runs the pipeline in temporary storage and leaves current exports unchanged.

![Sample analysis](images/sample-analysis.png)

## Decision context

A hypothetical retail planning analyst needs to decide what to investigate in a weekly review: demand changes, promotion performance and replenishment exceptions. This demonstration delivers an evidence-backed review queue, not purchasing decisions or real-company results.

## Observations → interpretation → action

| Question | Measured sample evidence | Suggested next action | What we cannot conclude |
|---|---|---|---|
| Where is demand concentrated? | Store {int(highest.store_nbr)} contributes {highest.total_sales:,.2f} of {total:,.2f} volume ({highest.total_sales / total:.1%}); all stores have 120 observed dates. | Start a store/family demand review there; check the category mix. | Higher volume does not imply higher profit or greater efficiency. Mixed category units are only a rough workload indicator. |
| Which family is relatively variable? | {most_variable.family.title()} has the largest daily family CV: {most_variable.coefficient_of_variation:.3f}. CV = sample standard deviation / mean, using daily totals across stores. | Inspect day-level spikes and individual stores before adjusting buffers. | CV alone does not measure forecast error or justify a service-level promise. |
| Which planning exceptions need review? | {int(counts['Reorder now'])} of {len(plan)} series fall below the assumed reorder point; {int(counts['Overstock risk'])} exceed the overstock threshold. | Verify actual stock, inbound orders and lead times before any order decision. | The sample deliberately creates equal risk counts. These are not observed stockouts or measured operational problems. |

### Promotion associations

Means below are per store/family/day observation. Unknown promotion status would be excluded from both groups. Percentage difference = 100 × (promoted mean / nonpromoted mean − 1).

| Family | Promoted rows | Other known rows | Promoted mean | Nonpromoted mean | Difference |
|---|---:|---:|---:|---:|---:|
"""
    for r in promotions.itertuples():
        text += f"| {r.family} | {r.promoted_rows} | {r.nonpromoted_rows} | {r.promoted_average:.2f} | {r.nonpromoted_average:.2f} | {r.lift_pct:+.1f}% |\n"
    text += """
Household's negative association is a prompt to inspect timing and store mix, not to cancel promotions. Produce's positive association is not proof of incremental demand. These patterns were generated deliberately; this exercise demonstrates a method, not a discovery about real shoppers. Prices and margins are absent, so promotion profitability cannot be evaluated.

## Trend chart interpretation

Compare each family's weekly volume with its own first full week (index 100). This avoids putting categories with different scales on one raw-volume axis. The 17 complete Monday–Sunday weeks are included; the final one-day week is excluded. The index shows relative changes, not absolute size, growth caused by promotions or forecast accuracy.

## Analysis workflow

1. **Question:** What should a planner investigate first, and what evidence supports that choice?
2. **Preparation:** Validate date/store/family uniqueness and nonnegative demand; retain unknowns instead of silently filling them with zero.
3. **Analysis:** Use SQL groupings, conditional averages and variability measures. Run [the business questions](../sql/business_questions.sql) against the generated DuckDB database.
4. **Communication:** Separate observations, assumptions and actions. Use the visual preview here; the actual Power BI report remains a manual build.
5. **Limits:** Synthetic data, category rather than SKU grain, assumed inventory/lead times, no prices and no forecast holdout. A sensible next step is real-data validation, not more infrastructure.

### Run the SQL examples

After running the sample pipeline, execute from the project root:

```bash
python - <<'SQL_DEMO'
from pathlib import Path
import duckdb
with duckdb.connect("data/processed/stockpilot.duckdb", read_only=True) as con:
    for query in con.extract_statements(Path("sql/business_questions.sql").read_text()):
        print(con.execute(query.query).df().to_string(index=False))
SQL_DEMO
```

### Project summary

StockPilot translates retail demand into a planning review using Python validation, SQL aggregation in DuckDB, and a simple trailing-average baseline for simulated replenishment scenarios. The Power BI model and reproducible analytical preview show how the outputs can support reporting, while the synthetic sample keeps the results clearly separated from real business outcomes.

Python and SQL make the calculations repeatable; Power BI is the planned presentation layer. The SQL examples, data-quality checks and inventory formulas provide reproducible checkpoints for the analysis.
"""
    brief_path = ROOT / "docs/SAMPLE_FINDINGS.md"
    brief_path.write_text(text)
    print(f"Created {image_path.relative_to(ROOT)} and {brief_path.relative_to(ROOT)}")


if __name__ == "__main__":
    build_brief()
