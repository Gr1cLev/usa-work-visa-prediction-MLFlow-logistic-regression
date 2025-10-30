from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib, os, pandas as pd, json, re
from pydantic import BaseModel, Field, field_validator

US = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","IA","ID","IL","IN","KS","KY","LA","MA","MD","ME","MI","MN","MO","MS","MT","NC","ND","NE","NH","NJ","NM","NV","NY","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VA","VT","WA","WI","WV","WY","DC"}

class Payload(BaseModel):
    FULL_TIME_POSITION: str = Field(pattern="^[YN]$")
    EMPLOYER_STATE: str
    WORKSITE_STATE: str
    SOC_CODE: str
    WAGE_RATE: float
    @field_validator("EMPLOYER_STATE","WORKSITE_STATE")
    @classmethod
    def v_state(cls,v): 
        v=v.upper(); 
        if v not in US: raise ValueError("invalid state"); 
        return v
    @field_validator("SOC_CODE")
    @classmethod
    def v_soc(cls,v):
        if not re.match(r"^\d{2}-\d{4}$", v): raise ValueError("invalid SOC code")
        return v

VER_PATH = os.getenv("VERSION_PATH","version.json")
@app.get("/version")
def version():
    try: return json.load(open(VER_PATH))
    except: return {"trained_at_utc": None, "f1": None}


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
    proba = _model.predict_proba(df)[0,1]
    return {"label": "CERTIFIED" if proba>=0.5 else "DENIED", "proba_certified": round(float(proba),4)}
