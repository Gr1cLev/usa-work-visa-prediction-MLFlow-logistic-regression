from pathlib import Path

import pandas as pd

from evidently import Report
from evidently.presets import DataDriftPreset, DataQualityPreset

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "processed" / "lca_labeled.csv"
OUT_HTML = BASE / "docs" / "report.html"


def main():
    df = pd.read_csv(DATA, low_memory=False)

    mid = len(df) // 2 if len(df) > 1 else 1
    ref = df.iloc[:mid].copy()
    cur = df.iloc[mid:].copy()

    report = Report(metrics=[DataQualityPreset(), DataDriftPreset()])
    snapshot = report.run(reference_data=ref, current_data=cur)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(OUT_HTML)
    print(f"[Monitoring] wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
