import os, re, json, urllib.parse, requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)

# CKAN endpoints
BASE_GSA = "https://api.gsa.gov/technology/datagov/v3/action/package_search"
BASE_CATALOG = "https://catalog.data.gov/api/3/action/package_search"
API_KEY = os.getenv("DATAGOV_API_KEY")

# hanya izinkan domain resmi DOL/OFLC
ALLOWED_DOMAINS = {
    "dol.gov",
    "www.dol.gov",
    "foreignlaborcert.doleta.gov",
    "www.foreignlaborcert.doleta.gov",
    "icert.doleta.gov",
    "www.icert.doleta.gov",
    "dolcontentdev.servicenowservices.com",
}

# beberapa query, karena penamaan paket sering beda-beda
QUERIES = [
    "H-1B Disclosure Data OFLC",
    "LCA Disclosure Data OFLC",
    "Office of Foreign Labor Certification H-1B",
    "OFLC performance data H-1B",
]

def _ckan_search(q: str, rows: int = 120):
    # kalau ada API key, coba GSA dulu; kalau tidak, langsung catalog
    bases = [BASE_GSA, BASE_CATALOG] if API_KEY else [BASE_CATALOG, BASE_GSA]
    last_err = None
    for base in bases:
        try:
            params = {"q": q, "rows": rows}
            headers = {}
            if "api.gsa.gov" in base and API_KEY:
                params["api_key"] = API_KEY
                headers["X-Api-Key"] = API_KEY
            r = requests.get(base, params=params, headers=headers, timeout=45)
            if r.status_code in (401, 403):
                last_err = r.text
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = str(e)
            continue
    return {"error": last_err, "result": {"results": []}}

def _domain_ok(url: str) -> bool:
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower()
        return any(netloc == d or netloc.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False

def search_oflc_lca_resources(year: str | None = None):
    results = []
    for q in QUERIES:
        data = _ckan_search(q, rows=120)
        for pkg in data.get("result", {}).get("results", []):
            for r in pkg.get("resources", []):
                name = (r.get("name") or r.get("title") or "").lower()
                url = (r.get("url") or "").strip()
                if not url:
                    continue
                if not _domain_ok(url):
                    # skip resource dari domain selain DOL/OFLC
                    continue
                if not any(url.lower().endswith(ext) for ext in (".csv", ".xlsx", ".xls", ".zip")):
                    continue
                # longgar: harus mengandung h-1b/lca + (disclosure/fy/data)
                if any(k in name for k in ("h-1b", "h1b", "lca")) and any(k in name for k in ("disclosure", "fy", "data")):
                    if (year is None) or (str(year) in name):
                        results.append({
                            "name": r.get("name") or r.get("title"),
                            "url": url
                        })
        if results:
            break
    # fallback: kalau pakai filter tahun tapi kosong, lepas filter
    if year and not results:
        return search_oflc_lca_resources(None)
    return results

def pick_latest_url(resources):
    best, best_year = None, -1
    for r in resources:
        nm = (r.get("name") or "")
        m = re.search(r"(?:FY|Fiscal\s*Year)[^\d]*(\d{4})", nm, re.I)
        y = int(m.group(1)) if m else -1
        if y >= best_year:
            best_year, best = y, r
    return best

if __name__ == "__main__":
    y = os.getenv("LCA_YEAR")
    res = search_oflc_lca_resources(y)
    latest = pick_latest_url(res) if res else None
    print(json.dumps({"picked": latest, "candidates": res[:10] if res else []}, indent=2, ensure_ascii=False))
