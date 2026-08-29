"""Generate deterministic SYNTHETIC demo CSVs using only Python's standard library."""
import csv
from datetime import date, timedelta
from pathlib import Path
import random

def main():
    out = Path(__file__).resolve().parents[1] / "data/sample"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    with (out / "train.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "date", "store_nbr", "family", "sales", "onpromotion"])
        row_id = 0
        for day in range(120):
            current = date(2024, 1, 1) + timedelta(days=day)
            for store in (1, 2, 3):
                for idx, family in enumerate(("GROCERY", "PRODUCE", "DAIRY", "HOUSEHOLD")):
                    promo = 3 if (day + store + idx) % 9 < 2 else 0
                    mean = [180, 100, 75, 35][idx] * (0.7 + 0.2*store)
                    mean *= (1.2 if current.weekday() >= 5 else 1) * (1 + day/1200)
                    mean *= (1.2 if promo and idx != 3 else 0.9 if promo else 1)
                    sales = max(0, round(rng.gauss(mean, mean*[0.12, 0.4, 0.18, 0.55][idx]), 2))
                    writer.writerow([row_id, current, store, family, sales, promo])
                    row_id += 1
    with (out / "stores.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["store_nbr", "city", "state", "type", "cluster"])
        writer.writerows([[1, "Demo North", "Demo", "A", 1], [2, "Demo Central", "Demo", "B", 1], [3, "Demo South", "Demo", "A", 2]])

if __name__ == "__main__":
    main()
