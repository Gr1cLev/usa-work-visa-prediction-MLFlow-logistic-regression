import os
import json 
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
ENV_CANDIDATES = [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
]
for candidate in ENV_CANDIDATES:
    if candidate.is_file():
        load_dotenv(dotenv_path=candidate)
        break
else:
    load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "artifacts/model.joblib")

app = FastAPI(title="Visa LCA Classifier (Demo)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestPayload(BaseModel):
    FULL_TIME_POSITION: str = Field(..., description="Y/N")
    EMPLOYER_STATE: str
    WORKSITE_STATE: str
    SOC_CODE: str
    WAGE_RATE: float

_model = None

@app.on_event("startup")
def startup():
    global _model
    if os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH).get("model")

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None}

@app.post("/predict")
def predict(p: RequestPayload):
    if _model is None:
        return {"error": "Model not loaded. Train first."}
    df = pd.DataFrame([p.dict()])
    proba = _model.predict_proba(df)[0, 1]

    result = {
        "label": "CERTIFIED" if proba >= 0.5 else "DENIED",
        "proba_certified": round(float(proba), 4)
    }

    try:
        with open("inference_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "req": p.dict(),
                "pred": result["label"],
                "proba": float(proba)
            }) + "\n")
    except Exception:
        pass

    return result
