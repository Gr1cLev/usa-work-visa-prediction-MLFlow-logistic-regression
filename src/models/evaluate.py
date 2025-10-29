import json, joblib, pandas as pd
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"
ART = BASE / "artifacts"
DOC = BASE / "docs"
DOC.mkdir(parents=True, exist_ok=True)

def main():
    df = pd.read_csv(PROC / "features.csv")
    model = joblib.load(ART / "model.joblib")["model"]
    y = df["CASE_STATUS_BIN"]; X = df.drop(columns=["CASE_STATUS_BIN"])
    yhat = model.predict(X)
    report = classification_report(y, yhat, output_dict=True)
    cm = confusion_matrix(y, yhat).tolist()
    (DOC / "eval.json").write_text(json.dumps({"report": report, "confusion_matrix": cm}, indent=2))
    print("[Eval] wrote docs/eval.json")

if __name__ == "__main__":
    main()
