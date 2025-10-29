# Visa LCA MLOps Portfolio (with Web UI)

End-to-end MLOps demo: ingest (CKAN Data.gov) → validate (Pandera) → features → train & track (MLflow) → evaluate → monitoring (Evidently) → serve (FastAPI) → UI (static, di `docs/ui`) → CI/CD (GitHub Actions), Pages, Hugging Face Spaces.

> Data: LCA Disclosure (proxy publik). Demo edukatif—bukan penentu keputusan nyata.

## Quickstart
```bash
pip install -r requirements.txt

# Pipeline
python -m src.data.ingest
python -m src.data.validate
python -m src.features.build_features
python -m src.models.train
python -m src.models.evaluate
python -m src.monitoring.generate_report

# API
uvicorn src.serving.app:app --reload --port 8000

# UI: buka docs/ui/index.html (double-click) atau via GitHub Pages
```

## Env vars opsional
- MAX_ROWS=50000, LCA_YEAR=2024, DATAGOV_API_KEY=YOUR_KEY

## Struktur
```
src/
  data/{ckan_fetch_latest.py, ingest.py, validate.py}
  features/build_features.py
  models/{train.py, evaluate.py}
  monitoring/generate_report.py
  serving/app.py
configs/{training.yaml, schema.yaml, thresholds.yaml}
docs/{index.html, report.html?, eval.json?}
docs/ui/{index.html, styles.css, script.js}
.github/workflows/{ci.yml, pages.yml, deploy-hf.yml}
artifacts/
```
