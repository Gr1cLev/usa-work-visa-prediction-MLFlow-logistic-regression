import os, re, requests, pandas as pd
from pathlib import Path
from .ckan_fetch_latest import search_oflc_lca_resources, pick_latest_url

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)


def _make_synthetic_dataset(max_rows: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "CASE_STATUS": ["CERTIFIED"]*60 + ["DENIED"]*20,
        "FULL_TIME_POSITION": ["Y"]*60 + ["N"]*20,
        "EMPLOYER_STATE": ["CA","TX","WA","NY","MA"]*16,
        "WORKSITE_STATE": ["CA","TX","WA","NY","MA"]*16,
        "SOC_CODE": ["15-1252","15-1245","15-1256","15-2051","11-1021"]*16,
        "WAGE_RATE": [120000.0,110000.0,130000.0,90000.0,145000.0]*16,
    }).head(max_rows)
    df["WAGE_RATE"] = df["WAGE_RATE"].astype(float)
    return df

def parse_wage(row):
    candidates = [k for k in row.index if "WAGE" in k and ("FROM" in k or "TO" in k)]
    vals = []
    for c in candidates:
        m = re.findall(r"[-+]?\d*\.?\d+", str(row[c]))
        if m:
            try: vals.append(float(m[0]))
            except: pass
    if vals:
        return sum(vals)/len(vals)
    for k in row.index:
        if "WAGE_RATE_OF_PAY" in k:
            m = re.findall(r"[-+]?\d*\.?\d+", str(row[k]))
            if m:
                try: return float(m[0])
                except: pass
    return None

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.upper().strip() for c in df.columns})
    want = ["CASE_STATUS","FULL_TIME_POSITION","EMPLOYER_STATE","WORKSITE_STATE","SOC_CODE"]
    for w in want:
        if w not in df.columns: df[w] = None
    if "WAGE_RATE" not in df.columns:
        df["WAGE_RATE"] = df.apply(parse_wage, axis=1)
    return df[want + ["WAGE_RATE"]].copy()

def load_table(path: Path, n=None):
    if path.suffix.lower() in [".xlsx",".xls"]:
        return pd.read_excel(path, nrows=n, engine="openpyxl")
    return pd.read_csv(path, nrows=n, low_memory=False)

def main():
    max_rows = int(os.getenv("MAX_ROWS","40000"))
    year = os.getenv("LCA_YEAR")
    resources = search_oflc_lca_resources(year)
    if not resources:
        print("[WARN] CKAN empty; creating synthetic sample...")
        df = _make_synthetic_dataset(max_rows)
        out = PROC / "lca_labeled.csv"
        df.to_csv(out, index=False)
        print(f"[Ingest] wrote {out} (synthetic)")
        return
    picked = pick_latest_url(resources)
    if not picked or not picked.get("url"):
        print("[WARN] invalid resource; making synthetic sample")
        df = _make_synthetic_dataset(max_rows)
        out = PROC / "lca_labeled.csv"
        df.to_csv(out, index=False)
        print(f"[Ingest] wrote {out} (synthetic)")
        return
    url = picked["url"]
    print(f"[Ingest] downloading {url}")
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] download failed: {e}; using synthetic sample")
        df = _make_synthetic_dataset(max_rows)
        out = PROC / "lca_labeled.csv"
        df.to_csv(out, index=False)
        print(f"[Ingest] wrote {out} (synthetic)")
        return
    dest = RAW / (url.split("/")[-1].split("?")[0] or "lca_download")
    dest.write_bytes(r.content)
    df0 = load_table(dest, n=max_rows)
    df = normalize_columns(df0)
    out = PROC / "lca_labeled.csv"
    df.to_csv(out, index=False)
    print(f"[Ingest] wrote {out} rows={len(df)}")

if __name__ == "__main__":
    main()
