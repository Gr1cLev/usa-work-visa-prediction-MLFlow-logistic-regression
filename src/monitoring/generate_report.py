from pathlib import Path
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"
DOCS = BASE / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

def main():
    feats = PROC / "features.csv"
    if not feats.exists():
        print("[Monitoring] features.csv not found.")
        return
    df = pd.read_csv(feats)
    n = len(df)
    if n < 10:
        print("[Monitoring] dataset too small for drift demo.")
        return
    ref = df.iloc[: int(0.7*n)].drop(columns=["CASE_STATUS_BIN"])
    cur = df.iloc[int(0.7*n):].drop(columns=["CASE_STATUS_BIN"])
    report = Report(metrics=[DataDriftPreset()])
    snapshot = report.run(reference_data=ref, current_data=cur)
    out = DOCS / "report.html"
    snapshot.save_html(out)
    print(f"[Monitoring] wrote {out}")

if __name__ == "__main__":
    main()
