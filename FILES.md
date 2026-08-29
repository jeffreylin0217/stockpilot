# Repository file inventory

Tracked source, test and documentation files:

```text
.gitignore
data/processed/.gitkeep
data/raw/.gitkeep
data/sample/README.md
data/sample/stores.csv
data/sample/train.csv
docs/ARCHITECTURE.md
docs/AUDIT.md
docs/INTERVIEW_GUIDE.md
docs/LEARNING_GUIDE.md
docs/RESUME_GUIDE.md
FILES.md
powerbi/exports/.gitkeep
powerbi/README.md
pyproject.toml
README.md
requirements.txt
scripts/export_powerbi.py
scripts/generate_sample.py
sql/bronze.sql
sql/gold.sql
sql/silver.sql
src/stockpilot/__init__.py
src/stockpilot/config.py
src/stockpilot/data_loader.py
src/stockpilot/forecasting.py
src/stockpilot/inventory.py
src/stockpilot/metrics.py
src/stockpilot/pipeline.py
src/stockpilot/recommendations.py
src/stockpilot/validation.py
tests/conftest.py
tests/test_inventory.py
tests/test_metrics.py
tests/test_pipeline.py
tests/test_powerbi_exports.py
tests/test_validation.py
```

Generated outputs under `data/processed/` and `powerbi/exports/` are intentionally ignored because they can be recreated.
