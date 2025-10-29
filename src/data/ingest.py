import os, re, io, zipfile, requests
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from .ckan_fetch_latest import search_oflc_lca_resources, pick_latest_url

BASE = Path(__file__).resolve().parents[2]
load_dotenv(BASE / ".env", override=False)

RAW  = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

REQ_OUT = ["CASE_STATUS","EMPLOYER_STATE","WORKSITE_STATE","SOC_CODE","FULL_TIME_POSITION","WAGE_RATE"]

def _make_synthetic_dataset(max_rows: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "CASE_STATUS": ["CERTIFIED"]*60 + ["DENIED"]*20,
        "FULL_TIME_POSITION": ["Y"]*60 + ["N"]*20,
        "EMPLOYER_STATE": ["CA","TX","WA","NY","MA"]*16,
        "WORKSITE_STATE": ["CA","TX","WA","NY","MA"]*16,
        "SOC_CODE": ["15-1252","15-1245","15-1256","15-2051","11-1021"]*16,
        "WAGE_RATE": [120000.0,110000.0,130000.0,90000.0,145000.0]*16,
    }).head(max_rows)
    return df

def _pick_col(df, *cands):
    lower = {c.lower(): c for c in df.columns}
    for k in cands:
        if k.lower() in lower:
            return lower[k.lower()]
    return None

def _std_soc(code):
    if pd.isna(code): return np.nan
    s = re.sub(r"\D", "", str(code))
    if len(s) == 6:
        return f"{s[:2]}-{s[2:]}"
    m = re.match(r"^\d{2}-\d{4}$", str(code))
    return str(code) if m else np.nan

def _parse_wage_cols(row):
    # coba FROM/TO
    cands = [c for c in row.index if "WAGE" in c and ("FROM" in c or "TO" in c)]
    vals = []
    for c in cands:
        m = re.findall(r"[-+]?\d*\.?\d+", str(row[c]))
        if m:
            try: vals.append(float(m[0]))
            except: pass
    if vals:
        return sum(vals)/len(vals)
    # coba WAGE_RATE_OF_PAY atau PREVAILING_WAGE
    for key in row.index:
        if "WAGE_RATE_OF_PAY" in key or "PREVAILING_WAGE" in key or key in ("WAGE", "WAGE_RATE"):
            m = re.findall(r"[-+]?\d*\.?\d+", str(row[key]))
            if m:
                try: return float(m[0])
                except: pass
    return np.nan

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: str(c).upper().strip() for c in df.columns})

    c_status = _pick_col(df, "CASE_STATUS","CASE STATUS","STATUS","CASESTATUS")
    emp_st   = _pick_col(df, "EMPLOYER_STATE","EMPLOYER STATE","EMPLOYER_STATE_ABBR","EMPLOYER STATE ABBR")
    work_st  = _pick_col(df, "WORKSITE_STATE","WORKSITE STATE","WORKSITE_STATE_ABBR","STATE_1","STATE")
    soc      = _pick_col(df, "SOC_CODE","SOC CODE","SOC","SOC-CODE")
    ft_pos   = _pick_col(df, "FULL_TIME_POSITION","FULL TIME POSITION","FULL_TIME_POSITION_Y_N","FT_FULL_TIME_POSITION")
    wage     = _pick_col(df, "WAGE_RATE","WAGE RATE","WAGE_RATE_OF_PAY","WAGE RATE OF PAY","PREVAILING_WAGE")

    out = pd.DataFrame(index=df.index)

    # CASE_STATUS
    out["CASE_STATUS"] = df[c_status].astype(str).str.strip().str.upper() if c_status else np.nan
    out["CASE_STATUS"] = out["CASE_STATUS"].replace({"CERTIFIED-WITHDRAWN":"CERTIFIED","WITHDRAWN":"DENIED"})

    # STATES
    out["EMPLOYER_STATE"]  = df[emp_st].astype(str).str.strip().str.upper() if emp_st else np.nan
    out["WORKSITE_STATE"]  = df[work_st].astype(str).str.strip().str.upper() if work_st else np.nan

    # SOC_CODE
    out["SOC_CODE"] = df[soc].apply(_std_soc) if soc else np.nan

    # FULL_TIME_POSITION
    if ft_pos:
        ft = df[ft_pos].astype(str).str.strip().str.upper().replace({
            "YES":"Y","NO":"N","TRUE":"Y","FALSE":"N","T":"Y","F":"N","1":"Y","0":"N"
        })
        out["FULL_TIME_POSITION"] = ft.str[0].where(ft.str[0].isin(["Y","N"]), np.nan)
    else:
        out["FULL_TIME_POSITION"] = np.nan

    # WAGE_RATE
    if wage:
        wr = pd.to_numeric(df[wage].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")
    else:
        wr = df.apply(_parse_wage_cols, axis=1)
    out["WAGE_RATE"] = wr

    # bersihkan baris kosong
    out = out.dropna(subset=REQ_OUT)
    return out[REQ_OUT].copy()

def _read_any(bytes_data: bytes, url: str, n=None) -> pd.DataFrame:
    url_l = url.lower()
    bio = io.BytesIO(bytes_data)
    if url_l.endswith(".csv"):
        return pd.read_csv(bio, nrows=n, low_memory=False, dtype=str)
    if url_l.endswith(".xlsx") or url_l.endswith(".xls"):
        # biarkan pandas pilih engine yang ada
        return pd.read_excel(bio, nrows=n, dtype=str)
    if url_l.endswith(".zip"):
        with zipfile.ZipFile(bio) as z:
            # ambil CSV pertama
            csvs = [f for f in z.namelist() if f.lower().endswith(".csv")]
            if not csvs:
                raise ValueError("ZIP tidak berisi CSV")
            with z.open(csvs[0]) as f:
                return pd.read_csv(f, nrows=n, low_memory=False, dtype=str)
    # fallback coba parse sebagai CSV
    return pd.read_csv(bio, nrows=n, low_memory=False, dtype=str)

def main():
    max_rows = int(os.getenv("MAX_ROWS", "40000"))
    year = os.getenv("LCA_YEAR")
    manual_url = os.getenv("LCA_URL")  # override manual jika ingin

    # 1) tentukan URL
    if manual_url:
        url = manual_url.strip()
        picked = {"name": "manual", "url": url}
        resources = [picked]
    else:
        resources = search_oflc_lca_resources(year)
        if not resources:
            print("[WARN] CKAN empty; creating synthetic sample...")
            df = _make_synthetic_dataset(max_rows)
            out = PROC / "lca_labeled.csv"
            df.to_csv(out, index=False)
            print(f"[Ingest] wrote {out} (synthetic)")
            return
        picked = pick_latest_url(resources) or resources[0]
        url = picked["url"]

    print(f"[Ingest] downloading {url}")
    try:
        r = requests.get(url, timeout=180)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] download failed: {e}; using synthetic sample")
        df = _make_synthetic_dataset(max_rows)
        out = PROC / "lca_labeled.csv"
        df.to_csv(out, index=False)
        print(f"[Ingest] wrote {out} (synthetic)")
        return

    # 2) simpan mentah
    fname = url.split("/")[-1].split("?")[0] or "lca_download"
    dest = RAW / fname
    dest.write_bytes(r.content)

    # 3) baca & normalisasi
    df0 = _read_any(r.content, url, n=max_rows)
    df = normalize_columns(df0)

    out = PROC / "lca_labeled.csv"
    df.to_csv(out, index=False)
    print(f"[Ingest] wrote {out} rows={len(df)}")

if __name__ == "__main__":
    main()
