import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score

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
    metrics = {
        "f1_macro": f1_score(y, yhat, average="macro"),
        "f1_weighted": f1_score(y, yhat, average="weighted"),
        "f1_positive": f1_score(y, yhat, pos_label=1),
    }
    payload = {"report": report, "confusion_matrix": cm, **metrics}
    (DOC / "eval.json").write_text(json.dumps(payload, indent=2))
    print("[Eval] wrote docs/eval.json")

if __name__ == "__main__":
    main()
