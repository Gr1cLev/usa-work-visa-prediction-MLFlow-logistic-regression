# usa-work-visa-prediction-ml-logistic-regression

This repository hosts a teaching project that estimates whether a United States work visa Labor Condition Application (LCA) is likely to be **certified** or **denied**. The classifier uses a logistic regression model and demonstrates an end-to-end MLOps workflow: data ingestion, validation, feature engineering, training with MLflow tracking, evaluation, monitoring with Evidently, and a FastAPI + static web UI for quick experiments.

> **Important:** this project is for learning only. The predictions are generated from public LCA disclosure data and a lightweight model. They are **not** a substitute for legal advice or official determinations.

## Explore Material
- Download the latest public LCA disclosure dataset from data.gov (or fall back to a synthetic sample if an API key is not provided).
- Validate input tables against a Pandera schema before training.
- Build features, train a logistic regression model, and log metrics to MLflow.
- Evaluate the trained model, export summary artifacts, and generate an Evidently data drift report.
- Serve predictions through a FastAPI endpoint and interact via the dropdown-friendly UI in `docs/ui`.

## Live demo
- **User interface** (GitHub Pages): https://gr1clev.github.io/usa-work-visa-prediction-MLFlow-logistic-regression/ui/
  When the page loads, set the "API Address" field to `https://gchrd-visa-lca-api.hf.space` before clicking **Predict**.
- **Prediction API** (Hugging Face Space): https://gchrd-visa-lca-api.hf.space/  
  A health check is available at `/health`, and predictions can be requested via `/predict` with a JSON payload.

## Quickstart
```bash
pip install -r requirements.txt

# Run the pipeline step by step
python -m src.data.ingest
python -m src.data.validate
python -m src.features.build_features
python -m src.models.train
python -m src.models.evaluate
python -m src.monitoring.generate_report

# Launch the API
uvicorn src.serving.app:app --reload --port 8000

# Open the web UI
# Option 1: double-click docs/ui/index.html
# Option 2: host via GitHub Pages or any static site host
```

## Environment variables
Set these in a `.env` file (see `.env.example`) or shell as needed:

| Variable | Purpose |
|----------|---------|
| `DATAGOV_API_KEY` | Required to fetch real LCA data from data.gov. Leave empty to fall back to the synthetic sample. |
| `DATA_GOV_API_URL` | (Optional) Override the CKAN endpoint. Defaults to the standard data.gov URL. |
| `LCA_YEAR` | (Optional) Prefer a specific fiscal year when searching for LCA resources. |
| `MAX_ROWS` | (Optional) Limit the number of rows ingested for quicker experiments. Defaults to 40000. |
| `MODEL_PATH` | (Optional) Path to the serialized model when serving. Defaults to `artifacts/model.joblib`. |

The serving app will automatically look for a `.env` file beside the executable or one directory above it (for example `/app/.env` or the project root). If none is present it simply relies on environment variables.

## Serving and deployment
- **Local FastAPI**: run `uvicorn src.serving.app:app --reload --port 8000` inside the project to expose the prediction API.
- **Docker / Hugging Face Space**: the `serving/` folder contains a lightweight Dockerfile and requirements file. It copies `app.py` and `model.joblib`, installs dependencies, and sets `MODEL_PATH` automatically. Push the folder to a Space (or build the image yourself) and the container will pick up `.env` if you add it next to `app.py`.
- **Static UI**: once the API is reachable, open `docs/ui/index.html` in a browser. Every input is a dropdown with an "Other" option so non-technical users can still enter custom values.


## Repository layout
```
src/
  data/{ckan_fetch_latest.py, ingest.py, validate.py}
  features/build_features.py
  models/{train.py, evaluate.py}
  monitoring/generate_report.py
  serving/app.py
configs/{training.yaml, schema.yaml, thresholds.yaml}
docs/{index.html, report.html, eval.json, ...}
docs/ui/{index.html, styles.css, script.js}
.github/workflows/{ci.yml, pages.yml, deploy-hf.yml}
artifacts/
```

