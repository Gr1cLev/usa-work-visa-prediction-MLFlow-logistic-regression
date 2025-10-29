from pathlib import Path
import pandas as pd

# Evidently (versi baru)
from evidently.report import Report
from evidently.metric_preset import DataQualityPreset, DataDriftPreset

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "processed" / "lca_labeled.csv"
OUT_HTML = BASE / "docs" / "report.html"

def main():
    df = pd.read_csv(DATA, low_memory=False)

    # bikin reference/current sederhana: bagi dua
    mid = len(df) // 2 if len(df) > 1 else 1
    ref = df.iloc[:mid].copy()
    cur = df.iloc[mid:].copy()

    report = Report(metrics=[
        DataQualityPreset(),   # missing values, types, dll.
        DataDriftPreset()      # deteksi drift antar ref vs current
    ])
    report.run(reference_data=ref, current_data=cur)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    report.save_html(str(OUT_HTML))
    print(f"[Monitoring] wrote {OUT_HTML}")

if __name__ == "__main__":
    main()
