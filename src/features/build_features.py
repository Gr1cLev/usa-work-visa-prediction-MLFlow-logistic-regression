import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"

def main():
    df = pd.read_csv(PROC / "lca_labeled.csv")
    df["CASE_STATUS_BIN"] = (df["CASE_STATUS"].astype(str).str.upper()=="CERTIFIED").astype(int)
    df["FULL_TIME_POSITION"] = df["FULL_TIME_POSITION"].fillna("U").astype(str).str.upper().str[0]
    for c in ["EMPLOYER_STATE","WORKSITE_STATE","SOC_CODE"]:
        df[c] = df[c].fillna("UNK").astype(str).str.upper()
    df["WAGE_RATE"] = pd.to_numeric(df["WAGE_RATE"], errors="coerce")
    df.to_csv(PROC / "features.csv", index=False)
    print("[Features] wrote features.csv", len(df))

if __name__ == "__main__":
    main()
