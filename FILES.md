# Exact deliverable file inventory

Paths are relative to the StockPilot project root.

```text
.gitignore
data/processed/.gitkeep
data/raw/.gitkeep
data/sample/README.md
data/sample/stores.csv
data/sample/train.csv
docs/ARCHITECTURE.md
docs/AUDIT.md
docs/images/sample-analysis.png
docs/SAMPLE_FINDINGS.md
FILES.md
powerbi/DATA_MODEL.md
powerbi/exports/.gitkeep
powerbi/measures.dax
powerbi/README.md
powerbi/REPORT_BUILD_GUIDE.md
powerbi/screenshots/.gitkeep
pyproject.toml
README.md
requirements-visuals.txt
requirements.txt
scripts/build_sample_brief.py
scripts/export_powerbi.py
scripts/generate_sample.py
sql/bronze.sql
sql/business_questions.sql
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

Generated files under `data/processed/` and `powerbi/exports/` are intentionally ignored except for `.gitkeep`. The reproducible sample brief and preview image are included so they display on GitHub.
